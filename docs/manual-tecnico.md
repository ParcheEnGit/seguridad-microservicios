# Manual técnico — LabSentinel

Guía para instalar, ejecutar, administrar y diagnosticar LabSentinel en un entorno local con Docker Compose. Las instrucciones corresponden a la rama `dev` (commit `111b503`).

## 1. Requisitos

| Categoría | Requisito |
| --- | --- |
| Sistema operativo | Windows 10/11, Linux o macOS con Docker Desktop o Docker Engine. |
| Hardware | Procesador de 4 núcleos (x86_64 o ARM64), 8 GB de RAM como mínimo (recomendado 16 GB) y unos 5 GB libres para imágenes y volúmenes. No se requieren sensores físicos: las lecturas las genera el simulador. |
| Software obligatorio | Git y Docker con Compose v2 (`docker compose version`). |
| Software opcional | Python 3.11+ para ejecutar las pruebas pytest; Node.js 22 LTS para ejecutar el frontend fuera de Docker; k6 para las pruebas de carga. |
| Cuenta externa | Un cliente OAuth de Google (tipo «Aplicación web») para el inicio de sesión. |
| Navegador | Chrome, Edge o Firefox actualizados. |

## 2. Componentes y puertos

| Contenedor | Función | Puerto en el host | Red |
| --- | --- | --- | --- |
| `gateway` (Nginx) | Punto de entrada único, proxy inverso y terminación TLS | `8080` (HTTPS) | frontend, backend |
| `frontend` (React + Vite) | Interfaz web (solo a través del gateway) | — | frontend |
| `auth-service` | Inicio de sesión (Keycloak y Google), sesión JWT y usuarios | — | frontend, backend |
| `device-service` | Dispositivos, umbrales y fotografías | — | backend |
| `telemetry-service` | Lecturas, evaluación de umbrales y avisos SMTP | — | backend, outbound |
| `alert-ticket-service` | Alertas y tickets | — | backend |
| `report-service` | Resúmenes para los dashboards | — | backend |
| `simulator-device` | Generador de lecturas simuladas | — | backend |
| `postgres` | Base de datos PostgreSQL 18 | — | backend |
| `database-migrations` | Aplica `infra/postgres/migrations/*.sql` y finaliza | — | backend |
| `keycloak` | Servidor de identidad con el realm `labsentinel` | `8081` (HTTPS) | frontend, backend |
| `tls-init` | Genera una CA local y el certificado de `localhost` en el volumen `tls_certificates` y finaliza | — | ninguna |
| `keycloak-client-config` | Sincroniza las URL HTTPS del cliente `labsentinel-web` en Keycloak y finaliza | — | backend |

El navegador se conecta por HTTPS (TLS 1.2/1.3) al gateway y a Keycloak con un certificado emitido por una CA local de desarrollo. Las claves se generan en un volumen de Docker y no se guardan en el repositorio. Dentro de la red de Docker, el gateway y los microservicios se comunican por HTTP.

La red `backend` es interna: los microservicios no son accesibles desde el host salvo a través del gateway. Aunque `compose.yaml` declara `5433:5432` para PostgreSQL, Docker no publica puertos de contenedores conectados solo a redes internas, por lo que la base no es accesible desde el host; se consulta con `docker compose exec postgres psql ...`.

> Nota: el inicio de sesión admite dos proveedores OpenID Connect. Con **Keycloak** (`KEYCLOAK_ENABLED=true`), `auth-service` usa el flujo Authorization Code con PKCE, verifica el ID token con las llaves públicas del realm (RS256, emisor y audiencia) y asigna el rol según los roles de realm `admin` o `lector`. Con **Google**, verifica el ID token de Google. En ambos casos, `auth-service` emite la misma cookie de sesión que validan los microservicios.

### Rutas del gateway

| Ruta pública | Servicio |
| --- | --- |
| `/` | frontend |
| `/api/auth/` | auth-service |
| `/api/devices/` | device-service |
| `/api/telemetry/` | telemetry-service |
| `/api/alerts-tickets/` | alert-ticket-service |
| `/api/reports/` | report-service |

## 3. Instalación y configuración

1. Clonar el repositorio y ubicarse en la rama de trabajo:

   ```powershell
   git clone https://github.com/ParcheEnGit/seguridad-microservicios.git
   cd seguridad-microservicios
   git checkout dev
   ```

2. Crear el archivo de entorno a partir del ejemplo (nunca subir `.env` al repositorio):

   ```powershell
   Copy-Item .env.example .env      # Windows
   cp .env.example .env             # Linux/macOS
   ```

3. Editar `.env` y reemplazar, como mínimo, las variables de la tabla siguiente.

| Variable | Descripción |
| --- | --- |
| `POSTGRES_PASSWORD`, `KEYCLOAK_DB_PASSWORD` | Contraseña local de PostgreSQL (ambas con el mismo valor). |
| `KEYCLOAK_ADMIN_PASSWORD` | Contraseña de la consola de Keycloak. |
| `JWT_SECRET` | Secreto de firma de la sesión; cadena aleatoria de al menos 32 caracteres. Todos los servicios usan el mismo valor. |
| `KEYCLOAK_ENABLED`, `VITE_KEYCLOAK_ENABLED` | `true` en ambas para habilitar el botón «Ingresar con Keycloak» (por defecto `false`). |
| `CORS_ORIGINS`, `COOKIE_SECURE`, `VITE_KEYCLOAK_URL` | Para HTTPS: `https://localhost:8080`, `true` y `https://localhost:8081`. Un `.env` creado antes de HTTPS debe actualizarse con estos valores. |
| `GOOGLE_CLIENT_ID`, `VITE_GOOGLE_CLIENT_ID` | ID del cliente OAuth de Google (el mismo valor en ambas). |
| `ADMIN_EMAILS` | Correo de Google del primer administrador (ver sección 5). |
| `SIMULATOR_API_KEY` | Clave técnica aleatoria que usa el simulador para enviar lecturas. |
| `SMTP_*`, `ALERT_EMAIL_RECIPIENTS` | Opcionales; solo si `SMTP_ENABLED=true`. |

4. Configurar el cliente OAuth en Google Cloud Console (APIs y servicios → Credenciales) con el origen JavaScript autorizado `https://localhost:8080`.

5. Después del primer `docker compose up -d`, confiar en la CA local para que el navegador no muestre advertencias (Windows, sin privilegios de administrador):

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/trust-local-labsentinel-ca.ps1
   ```

   Luego cerrar y volver a abrir el navegador.

## 4. Ejecución y administración

| Acción | Comando |
| --- | --- |
| Construir e iniciar todo | `docker compose up --build` (agregar `-d` para segundo plano) |
| Ver estado y salud | `docker compose ps` |
| Ver logs de un servicio | `docker compose logs -f <servicio>` |
| Reiniciar un servicio | `docker compose restart <servicio>` |
| Actualizar a la última versión | `git pull` y luego `docker compose up -d --build` |
| Reconstruir un servicio | `docker compose up -d --build <servicio>` |
| Consola SQL | `docker compose exec postgres psql -U labsentinel -d labsentinel` |
| Detener (conserva datos) | `docker compose down` |
| Detener y borrar datos | `docker compose down -v` (elimina base de datos, fotos y adjuntos) |
| Uso de CPU y RAM | `docker stats` |

El primer arranque descarga imágenes y puede tardar varios minutos. El orden de inicio se controla con `depends_on`: `tls-init` y PostgreSQL → migraciones y Keycloak → configuración del cliente de Keycloak → microservicios → simulador y gateway. Los microservicios tienen `healthcheck`, por lo que `docker compose ps` muestra `(healthy)` cuando responden en `/health`.

### Verificación

| Recurso | URL |
| --- | --- |
| Aplicación | `https://localhost:8080` |
| Consola de Keycloak | `https://localhost:8081` |
| Salud de servicios | `https://localhost:8080/api/devices/health`, `/api/telemetry/health`, `/api/alerts-tickets/health`, `/api/reports/health`, `/api/auth/health` |
| Usuario de la sesión (tras iniciar sesión) | `https://localhost:8080/api/auth/me` |
| Documentación OpenAPI de telemetría | `https://localhost:8080/api/telemetry/docs` |

Para exportar la especificación OpenAPI de cualquier servicio (por ejemplo, a la carpeta `contracts/`):

```powershell
docker compose exec device-service python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/openapi.json').read().decode())" > contracts/device-service.openapi.json
```

## 5. Usuarios y roles

LabSentinel maneja dos roles de aplicación, almacenados en la tabla `public.users` (columna `role`): `0` = administrador y `1` = lector.

1. **Primer administrador:** con la tabla de usuarios vacía, el primer inicio de sesión con Google de un correo incluido en `ADMIN_EMAILS` crea la cuenta con rol administrador.
2. **Demás usuarios:** el administrador los autoriza desde **Usuarios → Autorizar usuario** indicando nombre, correo y rol. Solo los correos autorizados pueden ingresar.
3. **Cambiar rol o revocar acceso:** desde la misma pantalla. El sistema impide quitar el último administrador o modificarse a sí mismo.

| Rol | Funciones disponibles |
| --- | --- |
| Administrador (`0`) | Inicio con resumen, Dispositivos (registro, edición, umbrales y fotos), Telemetría, Alertas (revisar y cerrar), Tickets (gestión), Reportes, Usuarios y `/peak` para forzar picos. |
| Lector (`1`) | Consulta de dispositivos, telemetría y alertas; creación y seguimiento de sus propios tickets. |

### Usuarios de Keycloak

1. Ingresar a `https://localhost:8081` con `KEYCLOAK_ADMIN` y `KEYCLOAK_ADMIN_PASSWORD`.
2. Seleccionar el realm `labsentinel` → **Users** → **Create user**, con correo electrónico obligatorio.
3. En la pestaña **Credentials**, asignar una contraseña; en **Role mapping**, asignar el rol de realm `admin` o `lector`.
4. En LabSentinel, presionar «Ingresar con Keycloak». Una cuenta sin uno de esos roles es rechazada.

El realm se importa solo cuando la base de Keycloak está vacía; los cambios posteriores en `infra/keycloak/realm-labsentinel.json` requieren recrear el volumen (`docker compose down -v`) o aplicarse desde la consola.

La sesión se guarda en la cookie HttpOnly `labsentinel_session`. Cada microservicio valida la firma y la expiración del token y aplica el rol requerido: responde `401` sin sesión o con un token inválido y `403` cuando el rol no tiene permiso.

### Acceso local de pruebas (opcional)

Para pruebas automatizadas sin Google, con `APP_ENV=development` y `LOCAL_PASSWORD_LOGIN_ENABLED=true` se habilita `POST /api/auth/password`. El usuario debe existir y tener una contraseña cifrada con bcrypt:

```powershell
docker compose exec auth-service python -c "import bcrypt; print(bcrypt.hashpw(b'ClaveDePrueba123', bcrypt.gensalt()).decode())"
docker compose exec postgres psql -U labsentinel -d labsentinel -c "UPDATE public.users SET password_hash='<hash>' WHERE email='lector@prueba.edu';"
```

No habilitar esta opción fuera del entorno local.

## 6. Simulador de telemetría

El `simulator-device` envía lecturas de todos los dispositivos con estado `activo` cada `SIMULATOR_INTERVAL_SECONDS` segundos (15 por defecto), autenticándose con la cabecera `X-Simulator-Key`. Los dispositivos nuevos se incorporan sin reiniciar el contenedor.

- Detener la generación sin borrar historial: `SIMULATOR_ENABLED=false` en `.env` y `docker compose up -d simulator-device`.
- Revisar envíos: `docker compose logs -f simulator-device`.
- Los administradores pueden forzar picos fuera de umbral desde la ruta `/peak` de la interfaz para demostrar la generación de alertas.

Más detalle en [conf-telemetria.md](conf-telemetria.md).

## 7. Pruebas

### Pruebas unitarias y de seguridad (pytest)

Se ejecutan fuera de Docker y no requieren la base de datos en marcha. Cada servicio tiene su propio `requirements.txt`:

```powershell
python -m venv .venv
.venv\Scripts\activate                 # Linux/macOS: source .venv/bin/activate
pip install pytest
cd services/alert-ticket-service; pip install -r requirements.txt; pytest -q; cd ../..
cd services/auth-service;         pip install -r requirements.txt; pytest -q; cd ../..
cd services/device-service;       pip install -r requirements.txt; pytest -q; cd ../..
cd services/report-service;       pip install -r requirements.txt; pytest -q; cd ../..
cd services/telemetry-service;    pip install -r requirements.txt; pytest -q; cd ../..
```

Si no se tiene Python instalado, [tests/README.md](../tests/README.md) explica cómo ejecutarlas dentro de un contenedor `python:3.11-slim`.

Resultado verificado el 27/10/2026 (commit `111b503`): alert-ticket-service 42 pruebas aprobadas, auth-service 3, device-service 18, report-service 11 y telemetry-service 53 (127 en total).

### Pruebas de carga (k6)

Con el sistema en ejecución y k6 instalado (escenario ligero sobre las rutas de salud):

```powershell
k6 run tests/performance/labsentinel-smoke.js
```

La prueba de carga autenticada (`tests/performance/labsentinel-load.js`) recorre sesión, dispositivos, alertas, historial y resumen administrativo con la cookie de un administrador. Puede ejecutarse sin instalar k6, con su imagen de Docker; las instrucciones y variables están en el encabezado del script. La cookie se pasa por variable de entorno y nunca se guarda en el repositorio.

El escenario y el registro de resultados están en [tests/performance/RESULTADOS.md](../tests/performance/RESULTADOS.md). Los casos, el plan y las evidencias se documentan en [plan-pruebas.md](plan-pruebas.md), [checklist-demostracion.md](checklist-demostracion.md) y [evidencias-demostracion.md](evidencias-demostracion.md).

## 8. Solución de problemas

| Problema | Posible causa | Solución |
| --- | --- | --- |
| Un contenedor no inicia | Puerto ocupado (8080, 8081), variable faltante en `.env` o imagen desactualizada. | Revisar `docker compose logs <servicio>`, liberar el puerto o cambiarlo en `.env` y ejecutar `docker compose up -d --build <servicio>`. |
| `password authentication failed` en migraciones o Keycloak | La contraseña del `.env` no coincide con la guardada en el volumen de PostgreSQL. | Alinear `POSTGRES_PASSWORD` y `KEYCLOAK_DB_PASSWORD` con las originales, o `docker compose down -v` (borra los datos). |
| `database-migrations` termina con error | Una migración falló o la base quedó en un estado inconsistente. | Revisar sus logs. En desarrollo, `docker compose down -v` y volver a iniciar (borra los datos). |
| Una ruta `/api/...` responde 404 o 502 después de recrear un servicio | Nginx conserva la IP anterior del contenedor recreado. | Ejecutar `docker compose restart gateway`. |
| `keycloak-client-config` termina con error y `auth-service` o `gateway` quedan en estado *Created* | Keycloak tardó más en iniciar que los reintentos del inicializador. | Ejecutar `docker compose up -d` nuevamente cuando Keycloak ya esté en ejecución. |
| El navegador muestra «La conexión no es privada» | La CA local de LabSentinel no es de confianza en el equipo. | Ejecutar `scripts/trust-local-labsentinel-ca.ps1` y reabrir el navegador. |
| No carga la página o falla el login después de actualizar a HTTPS | El `.env` conserva valores `http://` en `CORS_ORIGINS` o `VITE_KEYCLOAK_URL`. | Usar los valores HTTPS de `.env.example` y ejecutar `docker compose up -d --build`. |
| El botón de Google no aparece o responde 403 de origen | `VITE_GOOGLE_CLIENT_ID` vacío o el origen no está autorizado en Google Cloud. | Completar el ID en `.env`, agregar `https://localhost:8080` como origen y reiniciar `frontend`. |
| No aparece «Ingresar con Keycloak» | `VITE_KEYCLOAK_ENABLED` o `KEYCLOAK_ENABLED` siguen en `false`. | Poner ambas en `true` en `.env` y ejecutar `docker compose up -d --build frontend auth-service`. |
| «La cuenta no tiene un rol autorizado en Keycloak» | El usuario de Keycloak no tiene el rol de realm `admin` ni `lector`, o no tiene correo. | Asignar el rol en **Role mapping** y completar el correo del usuario en la consola de Keycloak. |
| «El correo no está autorizado» | El correo no fue autorizado por un administrador o la tabla ya tenía usuarios al usar `ADMIN_EMAILS`. | Autorizarlo desde **Usuarios**, o insertar el administrador directamente en `public.users`. |
| El usuario no es administrador | Se creó como lector o `ADMIN_EMAILS` estaba mal escrito. | Cambiar el rol desde **Usuarios** o con `UPDATE public.users SET role = 0 WHERE email = '...';` y volver a iniciar sesión. |
| Respuesta 401 inesperada | Sesión vencida o `JWT_SECRET` distinto entre servicios. | Cerrar e iniciar sesión; verificar que todos los servicios lean el mismo `.env`. |
| Respuesta 403 inesperada | El usuario tiene rol lector. | Cambiar el rol desde **Usuarios** y volver a iniciar sesión. |
| No llegan lecturas o los gráficos están vacíos | Simulador detenido, `SIMULATOR_ENABLED=false`, clave distinta o ningún dispositivo activo. | Revisar `docker compose logs simulator-device` y que exista al menos un dispositivo `activo`. |
| No se genera una alerta | El dispositivo no tiene umbral para esa métrica o ya existe una alerta abierta para la misma condición. | Revisar los umbrales del dispositivo y el estado de las alertas existentes. |
| No llegan correos de alerta | `SMTP_ENABLED=false` o credenciales SMTP inválidas. | Configurar `SMTP_*`; en Gmail usar una contraseña de aplicación. |

## 9. Limitaciones conocidas

- El certificado TLS lo emite una CA local de desarrollo, no una autoridad pública; para producción se requiere un certificado válido para el dominio real. El tráfico interno entre el gateway y los microservicios usa HTTP dentro de la red de Docker.
- Todos los servicios se conectan a PostgreSQL con el mismo usuario; la separación por servicio es lógica (esquemas `device_service`, `telemetry_service`, `alert_ticket_service` y `report_service`).
- La sesión dura 7 días (`JWT_EXPIRE_MINUTES=10080`). Un cambio de rol o una revocación se aplican cuando el usuario vuelve a iniciar sesión.
