# Servicios

Los servicios se ejecutan como contenedores FastAPI independientes. Keycloak y Nginx son componentes de infraestructura y viven en `infra/`.

- `device-service/`: dispositivos virtuales.
- `telemetry-service/`: lecturas enviadas por el simulador técnico.
- `alert-ticket-service/`: umbrales, alertas y tickets de lectores.
- `report-service/`: resúmenes y reportes protegidos.
- `simulator-device/`: perfil opcional; no envía datos hasta que el contrato de telemetría esté aprobado.
