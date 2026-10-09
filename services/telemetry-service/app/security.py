import hmac
import jwt

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import Settings, get_settings


def require_simulator_key(
    simulator_key: str | None = Header(default=None, alias="X-Simulator-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    if not simulator_key or not hmac.compare_digest(simulator_key, settings.simulator_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Componente simulador no autorizado")


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


def require_admin(claims: dict = Depends(get_current_claims)) -> dict:
    if claims.get("role") != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación es exclusiva para administradores",
        )
    return claims
