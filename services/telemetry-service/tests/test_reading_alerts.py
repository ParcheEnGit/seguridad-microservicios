import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")
os.environ.setdefault("SIMULATOR_API_KEY", "test-simulator-key")

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.security import require_simulator_key


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
