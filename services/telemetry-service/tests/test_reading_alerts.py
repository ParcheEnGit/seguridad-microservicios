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
from app.routes import classify_threshold_breach
from app.security import require_simulator_key

THRESHOLD = {
    "unit": "°c",
    "min_value": Decimal("18"),
    "max_value": Decimal("28"),
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
    def __init__(self, threshold, alert_insert=None, existing_alert=None):
        self.threshold = threshold
        self.alert_insert = alert_insert
        self.existing_alert = existing_alert
        self.committed = False
        self.statements = []
        self.reading = {
            "id": uuid.uuid4(),
            "device_id": uuid.uuid4(),
            "metric_code": "temperatura",
            "value": Decimal("29"),
            "unit": "°c",
            "equipment_status": None,
            "source": "simulador",
            "recorded_at": datetime.now(timezone.utc),
            "received_at": datetime.now(timezone.utc),
        }

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "FROM device_service.devices" in sql:
            return FakeResult({"id": self.reading["device_id"], "status": "activo"})
        if "FROM device_service.thresholds" in sql:
            return FakeResult(self.threshold)
        if "INSERT INTO telemetry_service.readings" in sql:
            return FakeResult({
                **self.reading,
                "device_id": params["device_id"],
                "metric_code": params["metric_code"],
                "value": params["value"],
                "unit": params["unit"],
                "recorded_at": params["recorded_at"],
            })
        if "INSERT INTO alert_ticket_service.alerts" in sql:
            return FakeResult(self.alert_insert)
        if "SELECT id, severity" in sql:
            return FakeResult(self.existing_alert)
        if "UPDATE alert_ticket_service.alerts" in sql:
            return FakeResult()
        raise AssertionError(f"SQL inesperado: {sql}")

    def commit(self):
        self.committed = True


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def post_reading(client, db, value="29"):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_simulator_key] = lambda: None
    return client.post(
        "/readings",
        json={
            "device_id": str(db.reading["device_id"]),
            "metric_code": "temperatura",
            "value": value,
            "unit": "°c",
        },
    )


def test_fuera_de_rango_crea_alerta_activa(client):
    alert_id = uuid.uuid4()
    db = FakeDatabase(
        threshold={
            "unit": "°c",
            "min_value": Decimal("18"),
            "max_value": Decimal("28"),
        },
        alert_insert={"id": alert_id},
    )

    response = post_reading(client, db)

    assert response.status_code == 201
    assert response.json()["out_of_range"] is True
    assert response.json()["condition"] == "above_max"
    assert response.json()["alert_id"] == str(alert_id)
    assert response.json()["alert_created"] is True
    assert db.committed
    assert any("ON CONFLICT (device_id, metric_code)" in sql for sql in db.statements)


def test_lectura_dentro_de_rango_no_crea_alerta(client):
    db = FakeDatabase(
        threshold={
            "unit": "°c",
            "min_value": Decimal("18"),
            "max_value": Decimal("28"),
        },
    )

    response = post_reading(client, db, value="24")

    assert response.status_code == 201
    assert response.json()["out_of_range"] is False
    assert response.json()["alert_id"] is None
    assert not any("INSERT INTO alert_ticket_service.alerts" in sql for sql in db.statements)
    assert db.committed


def test_alerta_activa_existente_no_se_duplica(client):
    existing_id = uuid.uuid4()
    db = FakeDatabase(
        threshold={
            "unit": "°c",
            "min_value": Decimal("18"),
            "max_value": Decimal("28"),
        },
        alert_insert=None,
        existing_alert={"id": existing_id, "severity": "advertencia"},
    )

    response = post_reading(client, db)

    assert response.status_code == 201
    assert response.json()["alert_id"] == str(existing_id)
    assert response.json()["alert_created"] is False
    assert db.committed


def test_lectura_critica_repetida_escala_alerta_existente(client):
    existing_id = uuid.uuid4()
    db = FakeDatabase(
        threshold=THRESHOLD,
        existing_alert={"id": existing_id, "severity": "advertencia"},
    )

    response = post_reading(client, db, value="30")

    assert response.status_code == 201
    assert response.json()["severity"] == "critica"
    assert response.json()["alert_created"] is False
    assert any("SET severity = 'critica'" in sql for sql in db.statements)


def test_lectura_advertencia_repetida_no_cambia_alerta_critica(client):
    db = FakeDatabase(
        threshold=THRESHOLD,
        existing_alert={"id": uuid.uuid4(), "severity": "critica"},
    )

    response = post_reading(client, db, value="28.5")

    assert response.status_code == 201
    assert response.json()["severity"] == "advertencia"
    assert not any("UPDATE alert_ticket_service.alerts" in sql for sql in db.statements)


def test_lectura_levemente_fuera_de_rango_crea_alerta_advertencia(client):
    db = FakeDatabase(threshold=THRESHOLD, alert_insert={"id": uuid.uuid4()})

    response = post_reading(client, db, value="28.5")

    assert response.status_code == 201
    assert response.json()["severity"] == "advertencia"
    assert response.json()["alert_created"] is True


def test_lectura_muy_fuera_de_rango_crea_alerta_critica(client):
    db = FakeDatabase(threshold=THRESHOLD, alert_insert={"id": uuid.uuid4()})

    response = post_reading(client, db, value="12")

    assert response.status_code == 201
    assert response.json()["condition"] == "below_min"
    assert response.json()["severity"] == "critica"
    assert response.json()["alert_created"] is True


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("18", None),
        ("28", None),
        ("23", None),
        ("28.99", ("above_max", "advertencia")),
        ("29", ("above_max", "critica")),
        ("17.01", ("below_min", "advertencia")),
        ("17", ("below_min", "critica")),
    ],
)
def test_clasificacion_de_severidad_en_los_limites(value, expected):
    assert classify_threshold_breach(
        Decimal(value),
        THRESHOLD["min_value"],
        THRESHOLD["max_value"],
    ) == expected
