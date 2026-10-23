# Resultados del escenario k6 (HU12)

## Cómo ejecutar

1. Levantar el stack: `docker compose up -d --build`
2. Instalar k6: https://k6.io/docs/get-started/installation/  
   En Windows (Chocolatey): `choco install k6`  
   O con el instalador MSI oficial.
3. Desde la raíz del repo:
   ```powershell
   k6 run tests/performance/labsentinel-smoke.js
   ```

## Escenario definido

| Parámetro | Valor por defecto |
|---|---|
| Script | `labsentinel-smoke.js` |
| VUs | 5 |
| Duración | 30 s |
| Objetivos | `/api/devices/health`, `/api/telemetry/health`, `/api/alerts-tickets/health`, `/api/reports/health` |
| Umbrales | `http_req_failed < 1%`, `p(95) < 800ms`, `checks > 99%` |

## Registro de ejecución

| Campo | Valor |
|---|---|
| Fecha | _(completar al ejecutar)_ |
| Commit | |
| `http_req_failed` | |
| `http_req_duration` p95 | |
| checks | |
| Notas | Pegar el resumen de k6 en `docs/evidencias-demostracion.md` |

> En el entorno del agente (octubre 2026) Docker Desktop y k6 no estaban disponibles; el script y los umbrales quedaron listos para ejecución local en la máquina de demostración.
