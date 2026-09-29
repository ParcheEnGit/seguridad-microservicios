# HU6: Simulación de telemetría

El `simulator-device` genera lecturas para todos los dispositivos con estado `activo`, incluidos los registrados antes de esta implementación y los que se agreguen posteriormente. Consulta los objetivos en cada ciclo, por lo que no necesita reiniciarse al crear un dispositivo.

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

## Demostración

```powershell
docker compose up -d --build
docker compose logs -f simulator-device
```

El log debe indicar cuántas lecturas se enviaron en cada ciclo. Luego, con una sesión iniciada, abra el Dashboard Admin o Dashboard Lector: ambos se actualizan cada 15 segundos. La documentación OpenAPI está disponible en `http://localhost:8080/api/telemetry/docs`.
