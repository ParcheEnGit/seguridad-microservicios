"""Pruebas de creación, trazabilidad y aislamiento de tickets entre lectores (HU9)."""
import os
import uuid
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")

import jwt
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

SECRET = os.environ["JWT_SECRET"]
READER_ID = 2
OTHER_READER_ID = 3
ADMIN_ID = 1
DEVICE_ID = uuid.uuid4()
VALID_FORM = {
    "device_id": str(DEVICE_ID),
    "category": "carcasa_rota",
    "description": "La carcasa del router tiene una grieta visible en la esquina.",
}


class FakeResult:
    def __init__(self, row=None, rows=None, scalar=None):
        self.row = row
        self.rows = rows if rows is not None else []
        self.scalar = scalar

    def mappings(self):
        return self

    def first(self):
        return self.row

    def all(self):
        return self.rows

    def scalar_one(self):
        return self.scalar


class FakeDatabase:
    def __init__(self, device_exists=True, ticket_owner_id=READER_ID):
        self.device_exists = device_exists
        self.ticket_id = uuid.uuid4()
        self.ticket_owner_id = ticket_owner_id
        self.ticket_insert = None
        self.history_insert = None
        self.list_sql = None
        self.list_params = None
        self.committed = False
        now = datetime(2026, 10, 9, 15, tzinfo=timezone.utc)
        self.history = [{
            "previous_status": None,
            "new_status": "abierto",
            "note": "Ticket registrado",
            "changed_at": now,
        }]
        self.ticket_row = {
            "id": self.ticket_id,
            "ticket_number": 1,
            "device_id": DEVICE_ID,
            "device_name": "Router laboratorio",
            "device_code": "RT-01",
            "category": "carcasa_rota",
            "description": VALID_FORM["description"],
            "status": "abierto",
            "created_by_user_id": ticket_owner_id,
            "created_at": now,
            "updated_at": now,
            "attachment_id": None,
            "attachment_name": None,
            "attachment_type": None,
            "attachment_size": None,
        }

    def execute(self, statement, params=None):
        sql = str(statement)
        if "SELECT id FROM device_service.devices" in sql:
            return FakeResult(row={"id": DEVICE_ID} if self.device_exists else None)
        if "INSERT INTO alert_ticket_service.tickets" in sql:
            self.ticket_insert = params
            self.ticket_row["created_by_user_id"] = params["user_id"]
            return FakeResult(scalar=self.ticket_id)
        if "INSERT INTO alert_ticket_service.ticket_status_history" in sql:
            self.history_insert = {"sql": sql, **params}
            return FakeResult()
        if "FROM alert_ticket_service.ticket_status_history" in sql:
            return FakeResult(rows=self.history)
        if "SELECT COUNT(*)" in sql:
            return FakeResult(scalar=1)
        if "WHERE t.id = :ticket_id" in sql:
            return FakeResult(row=self.ticket_row)
        if "FROM alert_ticket_service.tickets t" in sql:
            self.list_sql = sql
            self.list_params = params
            return FakeResult(rows=[self.ticket_row])
        raise AssertionError(f"SQL inesperado: {sql}")

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def client_for(db: FakeDatabase, user_id: int, role: int) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    client.cookies.set("labsentinel_session", jwt.encode({"sub": str(user_id), "role": role}, SECRET))
    return client


def teardown_function():
    app.dependency_overrides.clear()


def test_lector_registra_ticket_con_autor_y_primer_estado_trazable():
    db = FakeDatabase()

    response = client_for(db, READER_ID, role=1).post("/tickets", data=VALID_FORM)

    assert response.status_code == 201
    assert db.committed
    assert db.ticket_insert["user_id"] == READER_ID
    assert db.ticket_insert["device_id"] == DEVICE_ID
    assert db.history_insert["user_id"] == READER_ID
    assert "'abierto'" in db.history_insert["sql"]
    body = response.json()
    assert body["status"] == "abierto"
    assert body["code"] == "TK-2026-000001"
    assert body["history"][0]["previous_status"] is None
    assert body["history"][0]["new_status"] == "abierto"
    assert body["history"][0]["note"] == "Ticket registrado"


def test_ticket_para_dispositivo_inexistente_responde_404():
    db = FakeDatabase(device_exists=False)

    response = client_for(db, READER_ID, role=1).post("/tickets", data=VALID_FORM)

    assert response.status_code == 404
    assert db.ticket_insert is None
    assert not db.committed


def test_mis_tickets_solo_consulta_los_del_usuario_autenticado():
    db = FakeDatabase()

    response = client_for(db, READER_ID, role=1).get("/tickets/mine")

    assert response.status_code == 200
    assert "t.created_by_user_id = :user_id" in db.list_sql
    assert db.list_params["user_id"] == READER_ID


def test_lector_puede_ver_su_propio_ticket():
    db = FakeDatabase(ticket_owner_id=READER_ID)

    response = client_for(db, READER_ID, role=1).get(f"/tickets/{db.ticket_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(db.ticket_id)


def test_lector_no_puede_ver_ticket_de_otro_lector():
    db = FakeDatabase(ticket_owner_id=OTHER_READER_ID)

    response = client_for(db, READER_ID, role=1).get(f"/tickets/{db.ticket_id}")

    assert response.status_code == 404


def test_admin_puede_ver_ticket_de_cualquier_lector():
    db = FakeDatabase(ticket_owner_id=OTHER_READER_ID)

    response = client_for(db, ADMIN_ID, role=0).get(f"/tickets/{db.ticket_id}")

    assert response.status_code == 200
