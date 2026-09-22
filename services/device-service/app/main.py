import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router as device_router

SERVICE_NAME = os.getenv("SERVICE_NAME", "device-service")
app = FastAPI(title="LabSentinel Device Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(device_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"service": SERVICE_NAME, "status": "ok", "environment": os.getenv("APP_ENV", "development")}
