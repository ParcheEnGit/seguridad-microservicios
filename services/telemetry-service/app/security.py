import hmac

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


def require_simulator_key(
    simulator_key: str | None = Header(default=None, alias="X-Simulator-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    if not simulator_key or not hmac.compare_digest(simulator_key, settings.simulator_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Componente simulador no autorizado")
