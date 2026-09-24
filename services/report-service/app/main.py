import os

from fastapi import FastAPI

from app.routes import router as dashboard_router

SERVICE_NAME = os.getenv("SERVICE_NAME", "report-service")
app = FastAPI(title="LabSentinel Report Service", version="0.1.0")

app.include_router(dashboard_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"service": SERVICE_NAME, "status": "ok", "environment": os.getenv("APP_ENV", "development")}
