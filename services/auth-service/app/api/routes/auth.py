from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import AuthMessageResponse, GoogleLoginRequest, UserResponse
from app.auth.cookies import clear_session_cookie, set_session_cookie
from app.auth.dependencies import get_current_user
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
            detail="Unable to verify Google token. Check auth-service network access.",
        ) from exc

    user = UserRepository(db).get_or_create(
        google_id=google_profile["google_id"],
        email=google_profile["email"],
        name=google_profile["name"],
    )

    session_token = create_session_token(user, settings)
    set_session_cookie(response, session_token, settings)

    return AuthMessageResponse(
        message="Signed in successfully",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout")
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    clear_session_cookie(response, settings)
    return {"message": "Signed out successfully"}
