import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.migrate import apply_migrations
from app.db.session import engine

settings = get_settings()
SERVICE_NAME = os.getenv("SERVICE_NAME", settings.service_name)

app = FastAPI(title="LabSentinel Auth Service", version="0.1.0")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    apply_migrations(engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def redact_keycloak_callback_query(request: Request, call_next):
    """Evita que código de autorización y state queden en el access log.

    El handler aún recibe los parámetros durante `call_next`; se eliminan del
    scope inmediatamente antes de que Uvicorn escriba la línea de acceso.
    """
    response = await call_next(request)
    if request.url.path == "/auth/keycloak/callback":
        request.scope["query_string"] = b""
    return response

app.include_router(auth_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "environment": os.getenv("APP_ENV", settings.app_env),
    }
