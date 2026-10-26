"""Pruebas de permisos lector/admin en device-service (HU12).

La autorización se valida antes de persistir; las pruebas de 401/403 no necesitan BD real.
Ejecutar desde services/device-service:
    pip install -r requirements.txt pytest httpx
    pytest -q
"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")
os.environ.setdefault("DEVICE_IMAGES_PATH", "/tmp/device-images")

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402

SECRET = os.environ["JWT_SECRET"]
DEVICE_ID = uuid.uuid4()

CREATE_PAYLOAD = {
    "device_code": "SN-DEMO-01",
    "name": "Sensor demo",
    "device_type": "sensor",
    "location": "Lab A",
    "status": "activo",
    "thresholds": [
        {"metric_code": "temperatura", "unit": "°C", "min_value": 18, "max_value": 28},
    ],
}


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def unique(self):
        return self

    def __iter__(self):
        return iter(self._items)

    def all(self):
        return self._items


class FakeDatabase:
    def __init__(self):
        self.called = False

    def scalars(self, _statement):
        self.called = True
        return FakeScalars([])

    def scalar(self, _statement):
        self.called = True
        return 0


def client_with_role(role: int | None, db: FakeDatabase | None = None) -> TestClient:
    database = db or FakeDatabase()
    app.dependency_overrides[get_db] = lambda: database
    client = TestClient(app)
    if role is not None:
        client.cookies.set(
            "labsentinel_session",
            jwt.encode({"sub": "9", "role": role, "email": "demo@example.com"}, SECRET),
        )
    return client


def teardown_function():
    app.dependency_overrides.clear()


def test_listar_sin_sesion_responde_401():
    assert client_with_role(None).get("/devices").status_code == 401


def test_listar_con_token_invalido_responde_401():
    client = TestClient(app)
    client.cookies.set("labsentinel_session", "token.invalido")
    assert client.get("/devices").status_code == 401


def test_lector_puede_listar_dispositivos():
    db = FakeDatabase()
    response = client_with_role(1, db).get("/devices")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}
    assert db.called


def test_admin_puede_listar_dispositivos():
    response = client_with_role(0).get("/devices")
    assert response.status_code == 200


def test_lector_no_puede_crear_dispositivo():
    response = client_with_role(1).post("/devices", json=CREATE_PAYLOAD)
    assert response.status_code == 403


def test_sin_sesion_no_puede_crear_dispositivo():
    response = client_with_role(None).post("/devices", json=CREATE_PAYLOAD)
    assert response.status_code == 401


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("patch", f"/devices/{DEVICE_ID}", {"name": "Nuevo nombre"}),
        ("patch", f"/devices/{DEVICE_ID}/deactivate", {"status": "inactivo"}),
        ("put", f"/devices/{DEVICE_ID}/thresholds", [{"metric_code": "humedad", "unit": "%", "min_value": 40, "max_value": 70}]),
    ],
)
def test_lector_no_puede_escribir_dispositivo(method, path, body):
    client = client_with_role(1)
    response = getattr(client, method)(path, json=body)
    assert response.status_code == 403


def test_token_firmado_con_otra_clave_responde_401():
    client = TestClient(app)
    forged = jwt.encode({"sub": "1", "role": 0}, "otra-clave-que-no-es-la-del-servidor-123")
    client.cookies.set("labsentinel_session", forged)
    assert client.get("/devices").status_code == 401
