from fastapi import Response

from app.core.config import Settings


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    # HttpOnly prevents JavaScript access; Secure is disabled in local HTTP development.
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
