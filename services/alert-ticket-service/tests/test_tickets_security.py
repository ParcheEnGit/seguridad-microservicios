"""Pruebas de autorización y validación de tickets (HU9).

No necesitan base de datos: sesión, rol y datos del formulario se validan antes de consultar.
Ejecutar desde services/alert-ticket-service:
    pip install -r requirements.txt pytest
    pytest -q
"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-min-32-characters-long")

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

SECRET = os.environ["JWT_SECRET"]
VALID_FORM = {
    "device_id": str(uuid.uuid4()),
    "category": "carcasa_rota",
    "description": "La carcasa del router tiene una grieta visible en la esquina.",
}


def client_with_token(token: str | None) -> TestClient:
    client = TestClient(app)
    if token is not None:
        client.cookies.set("labsentinel_session", token)
    return client


def lector() -> TestClient:
    return client_with_token(jwt.encode({"sub": "2", "role": 1}, SECRET))


@pytest.mark.parametrize("method, url", [
    ("post", "/tickets"),
    ("get", "/tickets/mine"),
    ("get", f"/tickets/{uuid.uuid4()}"),
    ("get", f"/tickets/{uuid.uuid4()}/attachment"),
])
def test_sin_sesion_responde_401(method, url):
    response = getattr(client_with_token(None), method)(url)
    assert response.status_code == 401


def test_token_alterado_responde_401():
    assert client_with_token("token.alterado.invalido").post("/tickets", data=VALID_FORM).status_code == 401


def test_token_firmado_con_otra_clave_responde_401():
    forged = jwt.encode({"sub": "2", "role": 1}, "otra-clave-que-no-es-la-del-servidor-123")
    assert client_with_token(forged).get("/tickets/mine").status_code == 401


def test_rol_desconocido_responde_403():
    unknown = jwt.encode({"sub": "3", "role": 7}, SECRET)
    assert client_with_token(unknown).post("/tickets", data=VALID_FORM).status_code == 403


@pytest.mark.parametrize("field", ["device_id", "category", "description"])
def test_campos_obligatorios_responden_422(field):
    form = {key: value for key, value in VALID_FORM.items() if key != field}
    assert lector().post("/tickets", data=form).status_code == 422


def test_categoria_invalida_responde_422():
    assert lector().post("/tickets", data={**VALID_FORM, "category": "explosion"}).status_code == 422


def test_descripcion_corta_responde_422():
    response = lector().post("/tickets", data={**VALID_FORM, "description": "   corta   "})
    assert response.status_code == 422
    assert "al menos 10 caracteres" in response.json()["detail"]


def test_adjunto_con_tipo_no_permitido_responde_422():
    files = {"attachment": ("notas.txt", b"texto plano", "text/plain")}
    assert lector().post("/tickets", data=VALID_FORM, files=files).status_code == 422


def test_adjunto_que_no_coincide_con_su_firma_responde_422():
    files = {"attachment": ("falso.pdf", b"esto no es un pdf", "application/pdf")}
    assert lector().post("/tickets", data=VALID_FORM, files=files).status_code == 422


def test_adjunto_mayor_a_5mb_responde_422():
    files = {"attachment": ("grande.png", b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024), "image/png")}
    assert lector().post("/tickets", data=VALID_FORM, files=files).status_code == 422


def test_filtro_de_estado_invalido_responde_422():
    assert lector().get("/tickets/mine?status=perdido").status_code == 422
