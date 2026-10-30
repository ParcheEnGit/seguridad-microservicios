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
ALERT_ID = uuid.uuid4()
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

    def one_or_none(self):
        return self.row

    def all(self):
        return self.rows

    def scalar_one(self):
        return self.scalar


class FakeDatabase:
    def __init__(self, device_exists=True, ticket_owner_id=READER_ID, alert_device_id=DEVICE_ID, alert_severity="critica"):
        self.device_exists = device_exists
        self.alert_device_id = alert_device_id
        self.alert_severity = alert_severity
        self.ticket_id = uuid.uuid4()
        self.ticket_owner_id = ticket_owner_id
        self.ticket_insert = None
        self.history_insert = None
        self.status_update = None
        self.comment_insert = None
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
        self.comments = []
        self.ticket_row = {
            "id": self.ticket_id,
            "ticket_number": 1,
            "device_id": DEVICE_ID,
            "device_name": "Router laboratorio",
            "device_code": "RT-01",
            "category": "carcasa_rota",
            "description": VALID_FORM["description"],
            "priority": "no_critica",
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
        if "SELECT status FROM alert_ticket_service.tickets" in sql:
            return FakeResult(row={"status": self.ticket_row["status"]})
        if "SELECT id FROM alert_ticket_service.tickets" in sql:
            return FakeResult(row={"id": self.ticket_id})
        if "SELECT id FROM device_service.devices" in sql:
            return FakeResult(row={"id": DEVICE_ID} if self.device_exists else None)
        if "SELECT device_id, severity" in sql:
            return FakeResult(row={"device_id": self.alert_device_id, "severity": self.alert_severity})
        if "INSERT INTO alert_ticket_service.tickets" in sql:
            self.ticket_insert = params
            self.ticket_row["created_by_user_id"] = params["user_id"]
            self.ticket_row["priority"] = params["priority"]
            return FakeResult(scalar=self.ticket_id)
        if "INSERT INTO alert_ticket_service.ticket_status_history" in sql:
            self.history_insert = {"sql": sql, **params}
            if params.get("previous_status") is not None:
                self.history.append({
                    "previous_status": params["previous_status"],
                    "new_status": params["new_status"],
                    "note": params["note"],
                    "changed_at": self.ticket_row["updated_at"],
                    "changed_by_user_id": params["user_id"],
                    "changed_by_name": "Administrador de pruebas",
                })
            return FakeResult()
        if "UPDATE alert_ticket_service.tickets" in sql:
            self.status_update = params
            self.ticket_row["status"] = params["status"]
            return FakeResult()
        if "INSERT INTO alert_ticket_service.ticket_comments" in sql:
            self.comment_insert = params
            self.comments.append({
                "id": uuid.uuid4(),
                "author_user_id": params["user_id"],
                "author_name": "Administrador de pruebas",
                "comment": params["comment"],
                "created_at": self.ticket_row["updated_at"],
            })
            return FakeResult()
        if "FROM alert_ticket_service.ticket_status_history" in sql:
            return FakeResult(rows=self.history)
        if "FROM alert_ticket_service.ticket_comments" in sql:
            return FakeResult(rows=self.comments)
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
    assert body["priority"] == "no_critica"
    assert body["history"][0]["previous_status"] is None
    assert body["history"][0]["new_status"] == "abierto"
    assert body["history"][0]["note"] == "Ticket registrado"


def test_ticket_hereda_prioridad_critica_de_alerta():
    db = FakeDatabase()

    response = client_for(db, READER_ID, role=1).post(
        "/tickets",
        data={**VALID_FORM, "priority": "advertencia", "alert_id": str(ALERT_ID)},
    )

    assert response.status_code == 201
    assert db.ticket_insert["priority"] == "critica"
    assert response.json()["priority"] == "critica"


def test_ticket_hereda_prioridad_advertencia_de_alerta():
    db = FakeDatabase(alert_severity="advertencia")

    response = client_for(db, READER_ID, role=1).post(
        "/tickets",
        data={**VALID_FORM, "priority": "critica", "alert_id": str(ALERT_ID)},
    )

    assert response.status_code == 201
    assert db.ticket_insert["priority"] == "advertencia"
    assert response.json()["priority"] == "advertencia"


def test_ticket_no_se_crea_si_alerta_no_corresponde_al_dispositivo():
    db = FakeDatabase(alert_device_id=uuid.uuid4())

    response = client_for(db, READER_ID, role=1).post(
        "/tickets",
        data={**VALID_FORM, "alert_id": str(ALERT_ID)},
    )

    assert response.status_code == 422
    assert db.ticket_insert is None
    assert not db.committed


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


def test_admin_solo_puede_avanzar_la_transicion_permitida_y_queda_trazabilidad():
    db = FakeDatabase(ticket_owner_id=OTHER_READER_ID)

    response = client_for(db, ADMIN_ID, role=0).patch(
        f"/tickets/{db.ticket_id}/status",
        json={"status": "en_revision", "note": "Se inició la revisión física."},
    )

    assert response.status_code == 200
    assert db.status_update["status"] == "en_revision"
    assert db.history_insert["previous_status"] == "abierto"
    assert db.history_insert["new_status"] == "en_revision"
    assert db.history_insert["user_id"] == ADMIN_ID
    assert response.json()["history"][-1]["note"] == "Se inició la revisión física."


def test_admin_no_puede_saltar_transiciones_de_estado():
    db = FakeDatabase(ticket_owner_id=OTHER_READER_ID)

    response = client_for(db, ADMIN_ID, role=0).patch(
        f"/tickets/{db.ticket_id}/status",
        json={"status": "cerrado"},
    )

    assert response.status_code == 409
    assert db.status_update is None


def test_admin_agrega_comentario_trazable_al_ticket():
    db = FakeDatabase(ticket_owner_id=OTHER_READER_ID)

    response = client_for(db, ADMIN_ID, role=0).post(
        f"/tickets/{db.ticket_id}/comments",
        json={"comment": "Se coordinará una inspección presencial mañana."},
    )

    assert response.status_code == 200
    assert db.comment_insert["user_id"] == ADMIN_ID
    assert response.json()["comments"][0]["comment"] == "Se coordinará una inspección presencial mañana."


def test_bandeja_admin_aplica_filtros_de_estado_dispositivo_y_fecha():
    db = FakeDatabase(ticket_owner_id=OTHER_READER_ID)

    response = client_for(db, ADMIN_ID, role=0).get(
        f"/tickets?status=abierto&device_id={DEVICE_ID}&date_from=2026-10-01&date_to=2026-10-09",
    )

    assert response.status_code == 200
    assert "t.status = :status" in db.list_sql
    assert "t.device_id = :device_id" in db.list_sql
    assert "t.created_at >= :date_from" in db.list_sql
    assert "t.created_at < :date_to_exclusive" in db.list_sql
    assert db.list_params["device_id"] == DEVICE_ID


def test_bandeja_admin_rechaza_rango_de_fechas_invertido():
    db = FakeDatabase(ticket_owner_id=OTHER_READER_ID)

    response = client_for(db, ADMIN_ID, role=0).get("/tickets?date_from=2026-10-10&date_to=2026-10-01")

    assert response.status_code == 422
