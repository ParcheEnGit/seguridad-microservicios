# LabSentinel — Grupo 36

Plataforma telemática segura para el monitoreo de laboratorios mediante microservicios, OAuth 2.0/OIDC y contenedores.

## Stack tecnológico:

- Frontend: React + Vite + Lucide.
- Servicios: Python 3.11 + FastAPI.
- Identidad: Keycloak 26.7.3 con OAuth 2.0/OIDC y roles `admin`/`lector`.
- Gateway: Nginx.
- Persistencia: PostgreSQL 18.
- Infraestructura: Docker Compose.
- Pruebas: pytest/HTTPX y k6.

## Inicio rápido:

1. Instalar Docker Desktop y verificar `docker compose version`.
2. Copiar `.env.example` a `.env` y reemplazar todas las contraseñas locales.
3. Ejecutar `docker compose up --build`.
4. Abrir `http://localhost:8080` para LabSentinel y `http://localhost:8081` para la consola de Keycloak.
5. Comprobar los endpoints de salud mediante el gateway: `/api/devices/health`, `/api/telemetry/health`, `/api/alerts-tickets/health`, `/api/reports/health` y `/api/auth/me` (requiere sesión).
6. Configurar `GOOGLE_CLIENT_ID`, `VITE_GOOGLE_CLIENT_ID` y `JWT_SECRET` en `.env` para habilitar inicio de sesión con Google.

Keycloak importa el realm `labsentinel` al iniciar. Cree los usuarios de prueba y asigne los roles `admin` o `lector` desde su consola. No use contraseñas reales en desarrollo.

## Estructura:

```text
apps/frontend/                 React + Vite
services/device-service/       Inventario de dispositivos
services/telemetry-service/    Lecturas simuladas
services/alert-ticket-service/ Umbrales, alertas y tickets
services/report-service/       Vistas y reportes autorizados
services/simulator-device/     Simulador técnico (perfil opcional)
infra/keycloak/                Realm inicial
infra/nginx/                   API Gateway
infra/postgres/                Inicialización de base de datos
contracts/                     Contratos API antes de implementar endpoints
tests/                         Pruebas funcionales, seguridad y carga
```

## Reglas de seguridad:

- No subir `.env`, tokens, contraseñas ni secretos.
- Validar token y rol dentro de cada microservicio protegido; el gateway no es la única defensa.
- `admin` tiene control completo; `lector` consulta datos autorizados y crea tickets no críticos.
- El simulador es un cliente técnico distinto de los usuarios humanos.

## Trabajo colaborativo:

- `main`: entregas estables.
- `develop`: integración.
- `feature/<tema>`: una tarea concreta por rama.
- Pull request y revisión cruzada antes de fusionar a `develop`.

Consulte [docs/configuracion-inicial.md](docs/configuracion-inicial.md).
