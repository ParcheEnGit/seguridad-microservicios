import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes import router as alert_router
from app.tickets import router as ticket_router


SERVICE_NAME = os.getenv("SERVICE_NAME", "alert-ticket-service")
settings = get_settings()

app = FastAPI(
    title="LabSentinel Alert and Ticket Service",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(alert_router)
app.include_router(ticket_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "environment": os.getenv("APP_ENV", "development"),
    }
