# Pruebas — LabSentinel (HU12)

La evidencia se registra en `docs/plan-pruebas.md` y `docs/evidencias-demostracion.md`.

## Layout

| Ruta | Contenido |
|---|---|
| `services/*/tests/` | pytest + HTTPX (`TestClient`) por microservicio |
| `tests/performance/` | Escenario k6 de humo/carga inicial |
| `tests/security/` | Índice de casos de seguridad (enlaza a pytest) |

## Pytest / HTTPX (autenticación, permisos, lecturas, alertas y tickets)

Desde Git Bash en Windows (recomendado si no hay pytest local):

```bash
run_service_tests() {
  local service="$1"
  MSYS_NO_PATHCONV=1 docker run --rm \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$(pwd -W)/services/${service}:/src" \
    -w /src python:3.11-slim \
    sh -c "pip install -q -r requirements.txt pytest httpx && pytest -q -p no:warnings"
}

run_service_tests telemetry-service
run_service_tests alert-ticket-service
run_service_tests device-service
run_service_tests report-service
```

El contrato OIDC de `auth-service` no requiere base de datos ni un Keycloak
activo; se puede validar por separado con Python 3.11:

```powershell
Set-Location services/auth-service
$env:PYTHONPATH = $PWD.Path
uv run --python 3.11 --with-requirements requirements.txt python -m unittest discover -s tests -v
```

Cobertura esperada:

| Área | Archivos principales |
|---|---|
| Keycloak: PKCE, roles y claims | `auth-service/tests/test_keycloak.py` |
| Lecturas / umbrales / historial | `telemetry-service/tests/test_reading_*.py` |
| Alertas admin/lector | `alert-ticket-service/tests/test_alert_management.py` |
| Tickets | `alert-ticket-service/tests/test_tickets_security.py`, `test_ticket_traceability.py` |
| Dispositivos admin/lector | `device-service/tests/test_device_permissions.py` |
| Reportes admin | `report-service/tests/test_admin_summary_security.py` |

## k6 — escenario inicial

Instalación: https://k6.io/docs/get-started/installation/

```powershell
docker compose up -d --build
k6 run tests/performance/labsentinel-smoke.js
```

Variables opcionales: `BASE_URL`, `VUS`, `DURATION`.

```powershell
$env:VUS=10; $env:DURATION="1m"; k6 run tests/performance/labsentinel-smoke.js
```

## Seguridad (índice)

Ver [security/README.md](security/README.md).
