import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.security import get_current_claims


class FakeResult:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows if rows is not None else ([] if row is None else [row])

    def mappings(self):
        return self

    def one_or_none(self):
        return self.row

    def all(self):
        return self.rows


class FakeDatabase:
    def __init__(self, status="abierta"):
        self.alert_id = uuid.uuid4()
        self.reading_id = uuid.uuid4()
        self.status = status
        self.committed = False
        self.update_sql = None
        now = datetime.now(timezone.utc)
        self.alert = {
            "id": self.alert_id,
            "device_id": uuid.uuid4(),
            "device_name": "Sensor norte",
            "device_code": "SN-01",
            "reading_id": self.reading_id,
            "metric_code": "temperatura",
            "value": Decimal("30"),
            "unit": "°c",
            "threshold_min": Decimal("18"),
            "threshold_max": Decimal("28"),
            "condition": "above_max",
            "severity": "critica",
            "status": status,
            "created_at": now,
            "updated_at": now,
            "type": "temperatura",
            "deviceName": "Sensor norte",
            "date": now,
        }

    def execute(self, statement, params=None):
        sql = str(statement)
        if "SELECT status" in sql:
            return FakeResult({"status": self.status})
        if "UPDATE alert_ticket_service.alerts" in sql:
            self.update_sql = sql
            self.status = params["status"]
            self.alert["status"] = self.status
            return FakeResult()
        if "FROM telemetry_service.readings" in sql:
            return FakeResult({
                "id": self.reading_id,
                "metric_code": "temperatura",
                "value": Decimal("30"),
                "unit": "°c",
                "equipment_status": None,
                "source": "simulador",
                "recorded_at": datetime.now(timezone.utc),
                "received_at": datetime.now(timezone.utc),
                "payload": {},
            })
        if "FROM alert_ticket_service.alerts" in sql:
            if "LEFT JOIN device_service.devices" in sql:
                return FakeResult(self.alert, [self.alert])
        raise AssertionError(f"SQL inesperado: {sql}")

    def commit(self):
        self.committed = True


def setup_client(role=0, db=None):
    database = db or FakeDatabase()
    app.dependency_overrides[get_db] = lambda: database
    app.dependency_overrides[get_current_claims] = lambda: {"role": role, "sub": "7"}
    return TestClient(app), database


def teardown_function():
    app.dependency_overrides.clear()


def test_lista_alertas_incluye_campos_compatibles_con_dashboard():
    client, database = setup_client()
    response = client.get("/alerts")

    assert response.status_code == 200
    alert = response.json()[0]
    assert alert["deviceName"] == alert["device_name"] == "Sensor norte"
    assert alert["type"] == alert["metric_code"] == "temperatura"
    assert alert["date"] == alert["created_at"]
    assert alert["id"] == str(database.alert_id)


def test_detalle_incluye_lectura_que_genero_la_alerta():
    client, database = setup_client()
    response = client.get(f"/alerts/{database.alert_id}")

    assert response.status_code == 200
    assert response.json()["reading"]["id"] == str(database.reading_id)


def test_admin_puede_marcar_alerta_en_revision():
    client, database = setup_client(role=0)
    response = client.patch(
        f"/alerts/{database.alert_id}/status",
        json={"status": "revisada"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "revisada"
    assert database.committed


def test_lector_no_puede_cambiar_estado_de_alerta():
    client, database = setup_client(role=1)
    response = client.patch(
        f"/alerts/{database.alert_id}/status",
        json={"status": "revisada"},
    )

    assert response.status_code == 403
    assert not database.committed


def test_admin_puede_cerrar_alerta_revisada_y_conserva_quien_reviso():
    client, database = setup_client(role=0, db=FakeDatabase(status="revisada"))
    response = client.patch(
        f"/alerts/{database.alert_id}/status",
        json={"status": "cerrada"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cerrada"
    assert "resolved_by_user_id" in database.update_sql
    assert "reviewed_by_user_id" not in database.update_sql


def test_alerta_cerrada_no_puede_reabrirse():
    client, database = setup_client(role=0, db=FakeDatabase(status="cerrada"))
    response = client.patch(
        f"/alerts/{database.alert_id}/status",
        json={"status": "abierta"},
    )

    assert response.status_code == 409
    assert not database.committed


def test_alerta_abierta_no_puede_cerrarse_sin_revision():
    client, database = setup_client(role=0)
    response = client.patch(
        f"/alerts/{database.alert_id}/status",
        json={"status": "cerrada"},
    )

    assert response.status_code == 409
    assert not database.committed


def test_alerta_revisada_no_puede_volver_a_abierta():
    client, database = setup_client(role=0, db=FakeDatabase(status="revisada"))
    response = client.patch(
        f"/alerts/{database.alert_id}/status",
        json={"status": "abierta"},
    )

    assert response.status_code == 409
    assert not database.committed


def test_sin_sesion_no_puede_cambiar_estado():
    database = FakeDatabase()
    app.dependency_overrides[get_db] = lambda: database
    response = TestClient(app).patch(
        f"/alerts/{database.alert_id}/status",
        json={"status": "revisada"},
    )

    assert response.status_code == 401
    assert not database.committed
