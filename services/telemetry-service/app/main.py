import os

from fastapi import FastAPI

from app.routes import router as telemetry_router

SERVICE_NAME = os.getenv("SERVICE_NAME", "telemetry-service")
app = FastAPI(title="LabSentinel Telemetry Service", version="0.1.0")
app.include_router(telemetry_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"service": SERVICE_NAME, "status": "ok", "environment": os.getenv("APP_ENV", "development")}
