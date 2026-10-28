# LabSentinel — Grupo 36

Plataforma telemática segura para el monitoreo de laboratorios mediante microservicios, sesión JWT en cookie HttpOnly, Google OAuth y contenedores.

## Stack tecnológico

- Frontend: React + Vite + Lucide.
- Servicios: Python 3.11 + FastAPI.
- Autenticación: Google OAuth (ID token) + sesión JWT en cookie `labsentinel_session` (`auth-service`). Roles numéricos: `0` admin, `1` lector.
- Gateway: Nginx (entrada única en el puerto 8080).
- Persistencia: PostgreSQL 18 (esquemas por servicio).
- Infraestructura: Docker Compose.
- Pruebas: pytest + HTTPX (por servicio) y k6 (carga).

Keycloak es un proveedor de identidad opcional: cuando se habilita, `auth-service` usa
Authorization Code + PKCE S256 y conserva la misma sesión JWT HttpOnly interna. Google
continúa disponible mientras `KEYCLOAK_ENABLED=false`.

## Inicio rápido

1. Instalar Docker Desktop y verificar `docker compose version`.
2. Copiar `.env.example` a `.env` y reemplazar contraseñas, `JWT_SECRET`, `GOOGLE_CLIENT_ID`, `VITE_GOOGLE_CLIENT_ID` y `SIMULATOR_API_KEY`.
3. Ejecutar desde la raíz del repositorio:
   ```powershell
   docker compose up --build
   ```
4. Abrir `https://localhost:8080` (gateway + frontend).
   En el primer arranque, ejecutar `powershell -ExecutionPolicy Bypass -File scripts\trust-local-labsentinel-ca.ps1`
   para confiar la CA de desarrollo local generada por Docker.
5. Iniciar sesión con Google. El primer administrador se asigna con `ADMIN_EMAILS` (solo al crear el usuario).
6. Comprobar salud vía gateway:
   - `/api/devices/health`
   - `/api/telemetry/health`
   - `/api/alerts-tickets/health`
   - `/api/reports/health`
   - `/api/auth/me` (requiere sesión)

Guía detallada: [docs/configuracion-inicial.md](docs/configuracion-inicial.md).  
Arquitectura: [docs/arquitectura.md](docs/arquitectura.md).  
Manual técnico: [docs/manual-tecnico.md](docs/manual-tecnico.md).  
Checklist de demostración: [docs/checklist-demostracion.md](docs/checklist-demostracion.md).

## Variables de entorno esenciales

| Variable | Uso |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciales de PostgreSQL |
| `GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID` | Cliente OAuth de Google (mismo Client ID) |
| `JWT_SECRET` | Firma de la cookie de sesión (mínimo 32 caracteres) |
| `ADMIN_EMAILS` | Correos que reciben rol admin en el **primer** alta |
| `SIMULATOR_API_KEY` | Cabecera `X-Simulator-Key` del simulador |
| `SIMULATOR_ENABLED` / `SIMULATOR_INTERVAL_SECONDS` | Control del simulador |
| `CORS_ORIGINS` | Orígenes HTTPS permitidos (p. ej. `https://localhost:8080`) |
| `KEYCLOAK_ENABLED` / `VITE_KEYCLOAK_ENABLED` | Activa el acceso opcional con Keycloak en backend y UI |

Plantilla completa: [`.env.example`](.env.example). Nunca suba `.env` al repositorio.

## Puertos

| Recurso | URL / puerto |
|---|---|
| App (gateway) | `https://localhost:8080` |
| Frontend Vite | red Docker interna; no se publica directamente |
| Keycloak (opcional) | `https://localhost:8081` |
| Postgres (host) | `localhost:5433` → contenedor `5432` |
| OpenAPI telemetría | `https://localhost:8080/api/telemetry/docs` |

## Estructura

```text
apps/frontend/                 React + Vite
services/auth-service/         Google OAuth + sesión JWT
services/device-service/       Inventario y umbrales
services/telemetry-service/    Lecturas e historial
services/alert-ticket-service/ Alertas y tickets
services/report-service/       Resúmenes de dashboards
services/simulator-device/     Simulador técnico
infra/nginx/                   API Gateway
infra/postgres/                Migraciones e init
contracts/                     Contratos de API
tests/                         Índice de pruebas + k6
docs/                          Arquitectura, guías y demo
```

## Pruebas

```powershell
# Por servicio (ejemplo telemetría; requiere Docker o entorno Python 3.11)
MSYS_NO_PATHCONV=1 docker run --rm -v "${PWD}/services/telemetry-service:/src" -w /src python:3.11-slim sh -c "pip install -q -r requirements.txt pytest httpx && pytest -q"

# Carga inicial con k6 (instalar k6: https://k6.io/docs/get-started/installation/)
k6 run tests/performance/labsentinel-smoke.js
```

Detalle: [tests/README.md](tests/README.md).

## Reglas de seguridad

- No subir `.env`, tokens, contraseñas ni secretos.
- Cada microservicio valida la cookie JWT y el rol; el gateway no es la única defensa.
- `admin` (rol `0`) gestiona dispositivos, alertas y reportes; `lector` (rol `1`) consulta y crea tickets.
- El simulador es un cliente técnico autenticado con `X-Simulator-Key`, distinto de los usuarios humanos.

## Trabajo colaborativo

- `main`: entregas estables.
- `develop` / `dev`: integración.
- `feature/<tema>`: una tarea concreta por rama.
- Pull request y revisión cruzada antes de fusionar.
