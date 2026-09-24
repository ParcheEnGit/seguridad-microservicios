"""Pruebas de autorización del endpoint /dashboard/admin-summary (HU4).

No necesitan base de datos: la validación de sesión y rol ocurre antes de consultar.
Ejecutar desde services/report-service:
    pip install -r requirements.txt pytest
    pytest -q
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

SECRET = os.environ["JWT_SECRET"]
URL = "/dashboard/admin-summary"


def client_with_token(token: str | None) -> TestClient:
    client = TestClient(app)
    if token is not None:
        client.cookies.set("labsentinel_session", token)
    return client


def test_sin_sesion_responde_401():
    assert client_with_token(None).get(URL).status_code == 401


def test_token_alterado_responde_401():
    assert client_with_token("token.alterado.invalido").get(URL).status_code == 401


def test_token_firmado_con_otra_clave_responde_401():
    forged = jwt.encode({"sub": "1", "role": 0}, "otra-clave-que-no-es-la-del-servidor-123")
    assert client_with_token(forged).get(URL).status_code == 401


def test_lector_recibe_403():
    lector = jwt.encode({"sub": "2", "role": 1}, SECRET)
    assert client_with_token(lector).get(URL).status_code == 403
