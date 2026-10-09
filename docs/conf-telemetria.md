# HU6: Simulación de telemetría

El `simulator-device` genera lecturas para todos los dispositivos con estado `activo`, incluidos los registrados antes de esta implementación y los que se agreguen posteriormente. Consulta los objetivos en cada ciclo, por lo que no necesita reiniciarse al crear un dispositivo. Si aún no existe historial reciente, crea una muestra distribuida de siete días para que los gráficos no inicien vacíos.

## Configuración local

En `.env` se deben definir valores locales no versionados:

```dotenv
SIMULATOR_API_KEY=una-clave-aleatoria-de-desarrollo
SIMULATOR_INTERVAL_SECONDS=15
SIMULATOR_ENABLED=true
```

El intervalo mínimo es cinco segundos. Para detener solamente la generación, cambie `SIMULATOR_ENABLED=false` y reinicie el contenedor del simulador.

## Contrato de recepción

`POST /api/telemetry/readings` requiere la cabecera `X-Simulator-Key`. El servicio rechaza componentes no autorizados, dispositivos inexistentes, dispositivos que no estén activos y unidades incompatibles con un umbral existente.

```json
{
  "device_id": "uuid-del-dispositivo",
  "metric_code": "temperatura",
  "value": 24.6,
  "unit": "°c",
  "equipment_status": "operativo",
  "recorded_at": "2026-09-29T17:50:00Z"
}
```

Cuando el dispositivo tiene un umbral para la métrica, cada lectura se compara con `device_service.thresholds`. Las lecturas fuera del rango se guardan y generan una alerta en `alert_ticket_service.alerts`. Mientras exista una alerta `abierta` o `revisada` para el mismo dispositivo y métrica, las siguientes lecturas anómalas no crean duplicados. La respuesta incluye `out_of_range`, `condition`, `severity`, `alert_id` y `alert_created`.

La pantalla **Gestión de alertas** permite filtrar por dispositivo, severidad y estado, consultar la lectura asociada y, para administradores, marcar alertas en revisión o cerrarlas. La API de gestión está bajo `/api/alerts-tickets/alerts`; actualizar el estado usa `PATCH /api/alerts-tickets/alerts/{id}/status`.

## Demostración

```powershell
docker compose up -d --build
docker compose logs -f simulator-device
```

El log debe indicar cuántas lecturas se enviaron en cada ciclo. Luego, con una sesión iniciada, abra el Dashboard Admin o Dashboard Lector: ambos se actualizan cada 15 segundos. La documentación OpenAPI está disponible en `http://localhost:8080/api/telemetry/docs`.
