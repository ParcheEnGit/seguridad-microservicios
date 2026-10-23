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


def set_keycloak_login_cookies(response: Response, *, state: str, verifier: str, settings: Settings) -> None:
    """Guarda datos de una sola autorización OIDC fuera del alcance de JavaScript."""
    options = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "max_age": 600,
        "path": "/api/auth/keycloak/callback",
    }
    response.set_cookie(key=settings.keycloak_state_cookie_name, value=state, **options)
    response.set_cookie(key=settings.keycloak_verifier_cookie_name, value=verifier, **options)


def clear_keycloak_login_cookies(response: Response, settings: Settings) -> None:
    for name in (settings.keycloak_state_cookie_name, settings.keycloak_verifier_cookie_name):
        response.delete_cookie(
            key=name,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/api/auth/keycloak/callback",
        )
