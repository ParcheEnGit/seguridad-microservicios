# Manual técnico — LabSentinel

Instrucciones verificadas para ejecutar el prototipo en un entorno local con Docker Compose.

## Requisitos

| Ítem | Valor |
|---|---|
| Sistema operativo | Windows 10/11, macOS o Linux con Docker |
| Runtime | Docker Desktop + Compose v2 |
| Puertos libres | `8080` (app), `5173` (frontend), `8081` (Keycloak), `5433` (Postgres publicado) |
| Dependencias opcionales | k6 (carga), Node 22+ (frontend fuera de Docker), Python 3.11 (pytest local) |

Si el puerto `5432` de Windows ya lo usa otro PostgreSQL, LabSentinel publica Postgres en **`5433`**.

## Instalación

```powershell
git clone <url-del-repositorio>
cd seguridad-microservicios
Copy-Item .env.example .env
# Editar .env: contraseñas, Google Client ID, JWT_SECRET, SIMULATOR_API_KEY, ADMIN_EMAILS
docker compose up --build
```

## Administración

| Acción | Comando |
|---|---|
| Ver estado | `docker compose ps` |
| Logs del gateway | `docker compose logs -f gateway` |
| Logs del simulador | `docker compose logs -f simulator-device` |
| Detener | `docker compose down` |
| Reset de BD | `docker compose down -v` y volver a `up --build` |
| Consola SQL | `docker compose exec postgres psql -U labsentinel -d labsentinel` |

## Comprobación de salud

Con el stack levantado:

```powershell
curl http://localhost:8080/api/devices/health
curl http://localhost:8080/api/telemetry/health
curl http://localhost:8080/api/alerts-tickets/health
curl http://localhost:8080/api/reports/health
```

Tras login en el navegador, `GET /api/auth/me` debe devolver el usuario y el rol.

## Dashboards

1. Abrir `http://localhost:8080` e iniciar sesión con Google.
2. **Admin (rol 0):** Inicio con resumen, Dispositivos (escritura), Alertas (revisar/cerrar), Reportes, `/peak` para forzar picos.
3. **Lector (rol 1):** consulta de dispositivos/telemetría/alertas; creación de tickets en Tickets.

## Problemas frecuentes

| Síntoma | Causa probable | Acción |
|---|---|---|
| `password authentication failed` en migraciones/Keycloak | Contraseña del `.env` distinta a la del volumen | Alinear `POSTGRES_PASSWORD`/`KEYCLOAK_DB_PASSWORD` o `down -v` |
| Postgres no conecta desde DBeaver en `5433` | Contenedor solo en red interna / no publicado | Verificar `docker compose ps` → `0.0.0.0:5433->5432/tcp` |
| Login Google 403 origin | Origen no autorizado en Google Cloud | Añadir `http://localhost:8080` y `5173` |
| Usuario no es admin | `ADMIN_EMAILS` mal o usuario ya creado como lector | `UPDATE users SET role = 0 ...` y re-login |
| Frontend en `5174` | Otro proceso en `5173` | Detener el duplicado (Docker o `pnpm`) |
| No hay lecturas en gráficos | Simulador apagado o sin dispositivos activos | `SIMULATOR_ENABLED=true`, dispositivo `activo` con umbrales |

## Pruebas automatizadas y carga

Ver [tests/README.md](../tests/README.md).
