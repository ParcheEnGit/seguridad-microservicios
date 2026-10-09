"""Pruebas del historial de lecturas (HU7): orden, filtros, límite, autorización y resultados vacíos."""
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")
os.environ.setdefault("SIMULATOR_API_KEY", "test-simulator-key")

import jwt
import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

SECRET = os.environ["JWT_SECRET"]
DEVICE_ID = uuid.uuid4()
START = "2026-10-01T00:00:00Z"
END = "2026-10-02T00:00:00Z"


class FakeResult:
    def __init__(self, rows=None, scalar=None):
        self.rows = rows or []
        self.scalar = scalar

    def mappings(self):
        return self

    def all(self):
        return self.rows

    def scalar_one(self):
        return self.scalar


class FakeDatabase:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.history_sql = None
        self.history_params = None
        self.count_params = None

    def execute(self, statement, params=None):
        sql = str(statement)
        if "SELECT COUNT(*)" in sql:
            self.count_params = params
            return FakeResult(scalar=len(self.rows))
        if "FROM telemetry_service.readings" in sql:
            self.history_sql = sql
            self.history_params = params
            return FakeResult(rows=self.rows)
        raise AssertionError(f"SQL inesperado: {sql}")


def reading(minutes_ago: int, metric_code: str = "temperatura") -> dict:
    recorded_at = datetime(2026, 10, 1, 12, tzinfo=timezone.utc) - timedelta(minutes=minutes_ago)
    return {
        "id": uuid.uuid4(),
        "device_id": DEVICE_ID,
        "metric_code": metric_code,
        "value": Decimal("24.5"),
        "unit": "°c",
        "equipment_status": "operativo",
        "source": "simulador",
        "recorded_at": recorded_at,
        "received_at": recorded_at,
    }


def client_for(db: FakeDatabase, role: int | None = 1, secret: str = SECRET) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    if role is not None:
        client.cookies.set("labsentinel_session", jwt.encode({"sub": "5", "role": role}, secret))
    return client


def get_history(client: TestClient, **params):
    query = {"device_id": str(DEVICE_ID), "start_at": START, "end_at": END, **params}
    return client.get("/readings/history", params=query)


def teardown_function():
    app.dependency_overrides.clear()


def test_historial_se_ordena_de_la_lectura_mas_reciente_a_la_mas_antigua():
    rows = [reading(0), reading(15), reading(30)]
    db = FakeDatabase(rows)

    response = get_history(client_for(db))

    assert response.status_code == 200
    assert "ORDER BY recorded_at DESC" in db.history_sql
    recorded = [item["recorded_at"] for item in response.json()["items"]]
    assert recorded == sorted(recorded, reverse=True)


def test_filtros_de_dispositivo_metrica_y_fechas_llegan_a_la_consulta():
    db = FakeDatabase([reading(0)])

    response = get_history(client_for(db), metric_code="  Temperatura ")

    assert response.status_code == 200
    assert db.history_params["device_id"] == DEVICE_ID
    assert db.history_params["metric_code"] == "temperatura"
    assert db.history_params["start_at"] == datetime(2026, 10, 1, tzinfo=timezone.utc)
    assert db.history_params["end_at"] == datetime(2026, 10, 2, tzinfo=timezone.utc)
    assert db.count_params["metric_code"] == "temperatura"


def test_sin_filtro_de_metrica_consulta_todas_las_metricas():
    db = FakeDatabase([reading(0), reading(5, "humedad")])

    response = get_history(client_for(db))

    assert response.status_code == 200
    assert db.history_params["metric_code"] is None
    assert response.json()["total"] == 2


def test_limite_y_desplazamiento_se_aplican_y_se_devuelven():
    db = FakeDatabase([reading(0)])

    response = get_history(client_for(db), limit=10, offset=20)

    assert response.status_code == 200
    assert db.history_params["limit"] == 10
    assert db.history_params["offset"] == 20
    body = response.json()
    assert body["limit"] == 10
    assert body["offset"] == 20


def test_limite_por_defecto_es_50():
    db = FakeDatabase()

    response = get_history(client_for(db))

    assert response.json()["limit"] == 50
    assert db.history_params["limit"] == 50


@pytest.mark.parametrize("params", [
    {"limit": 0},
    {"limit": 101},
    {"offset": -1},
])
def test_limite_o_desplazamiento_fuera_de_rango_responde_422(params):
    db = FakeDatabase()

    response = get_history(client_for(db), **params)

    assert response.status_code == 422
    assert db.history_sql is None


def test_fecha_inicial_posterior_a_la_final_responde_422():
    db = FakeDatabase()

    response = get_history(client_for(db), start_at=END, end_at=START)

    assert response.status_code == 422
    assert db.history_sql is None


def test_dispositivo_con_identificador_invalido_responde_422():
    db = FakeDatabase()

    response = get_history(client_for(db), device_id="no-es-un-uuid")

    assert response.status_code == 422
    assert db.history_sql is None


def test_periodo_sin_lecturas_devuelve_lista_vacia():
    db = FakeDatabase([])

    response = get_history(client_for(db))

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


@pytest.mark.parametrize("role", [0, 1])
def test_admin_y_lector_pueden_consultar_el_historial(role):
    response = get_history(client_for(FakeDatabase([reading(0)]), role=role))

    assert response.status_code == 200


def test_sin_sesion_responde_401():
    db = FakeDatabase()

    response = get_history(client_for(db, role=None))

    assert response.status_code == 401
    assert db.history_sql is None


def test_sesion_firmada_con_otra_clave_responde_401():
    db = FakeDatabase()

    response = get_history(client_for(db, secret="otra-clave-que-no-es-la-del-servidor-123"))

    assert response.status_code == 401
    assert db.history_sql is None
