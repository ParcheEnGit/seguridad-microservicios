"""Sincroniza las URL locales HTTPS del cliente web de Keycloak.

El import de un realm no modifica un realm que ya existe en PostgreSQL. Este
inicializador conserva el cliente actual y actualiza solamente las URI de
retorno/orígenes que necesita el entorno HTTPS local.
"""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


BASE_URL = os.environ["KEYCLOAK_URL_INTERNAL"].rstrip("/")
REALM = os.environ["KEYCLOAK_REALM"]
CLIENT_ID = os.environ["KEYCLOAK_CLIENT_ID"]
REDIRECT_URI = os.environ["KEYCLOAK_REDIRECT_URI"]
FRONTEND_URL = os.environ["KEYCLOAK_FRONTEND_URL"].rstrip("/")


def request_json(path: str, *, method: str = "GET", payload: dict | None = None, token: str | None = None) -> object:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    with urlopen(request, timeout=8) as response:
        content = response.read()
        return json.loads(content.decode()) if content else None


def admin_token() -> str:
    body = urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": os.environ["KEYCLOAK_ADMIN"],
        "password": os.environ["KEYCLOAK_ADMIN_PASSWORD"],
    }).encode()
    request = Request(
        f"{BASE_URL}/realms/master/protocol/openid-connect/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode())["access_token"]


def main() -> None:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            token = admin_token()
            clients = request_json(
                f"/admin/realms/{quote(REALM)}/clients?clientId={quote(CLIENT_ID)}",
                token=token,
            )
            if not isinstance(clients, list) or not clients:
                raise RuntimeError(f"No se encontró el cliente {CLIENT_ID!r} en el realm {REALM!r}")
            client = clients[0]
            attributes = dict(client.get("attributes") or {})
            attributes["post.logout.redirect.uris"] = f"{FRONTEND_URL}/*"
            client["redirectUris"] = [REDIRECT_URI]
            client["webOrigins"] = [FRONTEND_URL]
            client["attributes"] = attributes
            request_json(
                f"/admin/realms/{quote(REALM)}/clients/{quote(str(client['id']))}",
                method="PUT",
                payload=client,
                token=token,
            )
            print(f"Cliente {CLIENT_ID} sincronizado para HTTPS local.", flush=True)
            return
        except (HTTPError, URLError, KeyError, RuntimeError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2)
    raise SystemExit(f"No se pudo sincronizar el cliente Keycloak: {last_error}")


if __name__ == "__main__":
    main()
