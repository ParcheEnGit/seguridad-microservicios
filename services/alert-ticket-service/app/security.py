import jwt
from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings


def get_current_claims(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    token = request.cookies.get(settings.cookie_name)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación",
        )

    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada",
        ) from exc


ROLE_ADMIN = 0
ROLE_READER = 1


def require_ticket_author(claims: dict = Depends(get_current_claims)) -> dict:
    """Admin y lector pueden registrar y consultar sus propios tickets."""
    if claims.get("role") not in (ROLE_ADMIN, ROLE_READER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para gestionar tickets",
        )
    try:
        claims["user_id"] = int(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada",
        ) from exc
    return claims
