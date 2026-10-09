"""Pruebas de recepción de lecturas del simulador (HU6): autorización, dispositivo y datos."""
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")
os.environ.setdefault("SIMULATOR_API_KEY", "test-simulator-key")

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

SIMULATOR_KEY = os.environ["SIMULATOR_API_KEY"]
DEVICE_ID = uuid.uuid4()
VALID_READING = {
    "device_id": str(DEVICE_ID),
    "metric_code": "temperatura",
    "value": "24.5",
    "unit": "°C",
    "equipment_status": "operativo",
    "recorded_at": "2026-10-01T12:00:00Z",
}


class FakeResult:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def one_or_none(self):
        return self.row

    def one(self):
        return self.row


class FakeDatabase:
    def __init__(self, device_status="activo", threshold=None):
        self.device = None if device_status is None else {"id": DEVICE_ID, "status": device_status}
        self.threshold = threshold
        self.inserted_reading = None
        self.committed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        if "FROM device_service.devices" in sql:
            return FakeResult(self.device)
        if "FROM device_service.thresholds" in sql:
            return FakeResult(self.threshold)
        if "INSERT INTO telemetry_service.readings" in sql:
            self.inserted_reading = params
            now = datetime.now(timezone.utc)
            return FakeResult({
                "id": uuid.uuid4(),
                "device_id": params["device_id"],
                "metric_code": params["metric_code"],
                "value": params["value"],
                "unit": params["unit"],
                "equipment_status": params["equipment_status"],
                "source": "simulador",
                "recorded_at": params["recorded_at"],
                "received_at": now,
            })
        raise AssertionError(f"SQL inesperado: {sql}")

    def commit(self):
        self.committed = True


def post_reading(db: FakeDatabase, payload: dict | None = None, key: str | None = SIMULATOR_KEY):
    app.dependency_overrides[get_db] = lambda: db
    headers = {"X-Simulator-Key": key} if key is not None else {}
    return TestClient(app).post("/readings", json=payload or VALID_READING, headers=headers)


def teardown_function():
    app.dependency_overrides.clear()


def test_simulador_autorizado_registra_lectura_valida():
    db = FakeDatabase()

    response = post_reading(db)

    assert response.status_code == 201
    assert response.json()["source"] == "simulador"
    assert response.json()["out_of_range"] is False
    assert db.inserted_reading["metric_code"] == "temperatura"
    assert db.inserted_reading["unit"] == "°c"
    assert db.committed


@pytest.mark.parametrize("key", [None, "", "clave-incorrecta"])
def test_sin_clave_de_simulador_valida_responde_401(key):
    db = FakeDatabase()

    response = post_reading(db, key=key)

    assert response.status_code == 401
    assert db.inserted_reading is None


def test_dispositivo_inexistente_responde_404():
    db = FakeDatabase(device_status=None)

    response = post_reading(db)

    assert response.status_code == 404
    assert db.inserted_reading is None


@pytest.mark.parametrize("device_status", ["inactivo", "mantenimiento"])
def test_dispositivo_no_activo_responde_409(device_status):
    db = FakeDatabase(device_status=device_status)

    response = post_reading(db)

    assert response.status_code == 409
    assert db.inserted_reading is None


def test_unidad_distinta_al_umbral_responde_422():
    db = FakeDatabase(threshold={"unit": "%", "min_value": Decimal("40"), "max_value": Decimal("70")})

    response = post_reading(db)

    assert response.status_code == 422
    assert db.inserted_reading is None


@pytest.mark.parametrize("change", [
    {"device_id": "no-es-un-uuid"},
    {"value": "no-es-un-numero"},
    {"value": "NaN"},
    {"metric_code": ""},
    {"metric_code": "   "},
    {"unit": ""},
    {"metric_code": "m" * 51},
    {"equipment_status": "e" * 31},
])
def test_datos_invalidos_responden_422(change):
    db = FakeDatabase()

    response = post_reading(db, {**VALID_READING, **change})

    assert response.status_code == 422
    assert db.inserted_reading is None


@pytest.mark.parametrize("field", ["device_id", "metric_code", "value", "unit"])
def test_campos_obligatorios_responden_422(field):
    db = FakeDatabase()
    payload = {key: value for key, value in VALID_READING.items() if key != field}

    response = post_reading(db, payload)

    assert response.status_code == 422
    assert db.inserted_reading is None
