import bcrypt

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import AuthMessageResponse, GoogleLoginRequest, PasswordLoginRequest, UserResponse
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

    user = UserRepository(db).get_or_create(
        google_id=google_profile["google_id"],
        email=google_profile["email"],
        name=google_profile["name"],
        picture_url=google_profile.get("picture_url"),
        admin_emails=settings.admin_email_set,
    )

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


@router.post("/logout")
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    clear_session_cookie(response, settings)
    return {"message": "Signed out successfully"}
