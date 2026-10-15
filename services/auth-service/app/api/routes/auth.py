import bcrypt

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas.auth import AuthMessageResponse, GoogleLoginRequest, PasswordLoginRequest, UserInviteCreate, UserResponse, UserRoleUpdate
from app.auth.cookies import clear_session_cookie, set_session_cookie
from app.auth.dependencies import get_current_admin, get_current_user
from app.auth.google import GoogleTokenVerificationError, verify_google_id_token
from app.auth.jwt_utils import create_session_token
from app.core.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health")
def auth_health() -> dict[str, str]:
    return {"service": "auth-service", "status": "ok"}



@router.post("/password", response_model=AuthMessageResponse)
def login_with_local_password(
    payload: PasswordLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthMessageResponse:
    """Acceso local de pruebas; no se habilita fuera de development."""
    if settings.app_env != "development" or not settings.local_password_login_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceso local no disponible")
    user = UserRepository(db).get_by_email(payload.email.strip().lower())
    valid_password = bool(
        user
        and user.password_hash
        and bcrypt.checkpw(payload.password.encode(), user.password_hash.encode())
    )
    if not valid_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos")
    set_session_cookie(response, create_session_token(user, settings), settings)
    return AuthMessageResponse(message="Sesión iniciada correctamente", user=UserResponse.model_validate(user))


@router.post("/google", response_model=AuthMessageResponse)
def login_with_google(
    payload: GoogleLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthMessageResponse:
    try:
        google_profile = verify_google_id_token(payload.credential, settings)
    except GoogleTokenVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo verificar el token de Google. Revise la conexión del servicio de autenticación.",
        ) from exc

    try:
        user = UserRepository(db).get_or_create(
            google_id=google_profile["google_id"],
            email=google_profile["email"],
            name=google_profile["name"],
            picture_url=google_profile.get("picture_url"),
            admin_emails=settings.admin_email_set,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    session_token = create_session_token(user, settings)
    set_session_cookie(response, session_token, settings)

    return AuthMessageResponse(
        message="Sesión iniciada correctamente",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/admin/panel", response_model=dict[str, str])
def read_admin_panel(current_user: User = Depends(get_current_admin)) -> dict[str, str]:
    return {
        "message": "Admin panel access granted",
        "email": current_user.email,
    }


@router.get("/users", response_model=list[UserResponse], summary="Listar usuarios autorizados")
def list_authorized_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[User]:
    return UserRepository(db).list_users()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Autorizar un usuario para su primer acceso con Google",
)
def create_authorized_user(
    payload: UserInviteCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> User:
    repository = UserRepository(db)
    email = str(payload.email).lower()
    if repository.get_by_email(email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese correo ya está autorizado")
    try:
        return repository.invite(name=payload.name, email=email, role=payload.role)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese correo ya está autorizado") from exc


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revocar el acceso de un usuario")
def delete_authorized_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> Response:
    repository = UserRepository(db)
    target = repository.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if target.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes revocar tu propio acceso mientras tienes una sesión activa",
        )
    if target.role == 0 and repository.count_administrators() <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Debe permanecer al menos un administrador autorizado",
        )
    repository.delete(target)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/users/{user_id}/role", response_model=UserResponse, summary="Cambiar el rol de un usuario autorizado")
def update_authorized_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> User:
    repository = UserRepository(db)
    target = repository.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if target.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes cambiar tu propio rol mientras tienes una sesión activa",
        )
    if target.role == payload.role:
        return target
    if target.role == 0 and payload.role == 1 and repository.count_administrators() <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Debe permanecer al menos un administrador autorizado",
        )
    return repository.update_role(target, payload.role)


@router.post("/logout")
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    clear_session_cookie(response, settings)
    return {"message": "Signed out successfully"}
