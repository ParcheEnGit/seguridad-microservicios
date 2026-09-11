# Selección de tecnologías y protocolos

| Componente | Alternativas consideradas | Selección | Justificación |
| --- | --- | --- | --- |
| Servicios | Node.js/Express, Flask/FastAPI, Spring Boot | Python 3.11 + FastAPI | Validación, documentación OpenAPI y curva de aprendizaje adecuada. |
| Frontend | HTML estático, Vue, React | React + Vite | Componentes reutilizables para vistas admin y lector. |
| Gateway | Kong, gateway propio, Nginx | Nginx | Proxy inverso ligero y entrada única. |
| Identidad | JWT manual, OAuth/OIDC con proveedor | Keycloak OAuth 2.0/OIDC | Roles, usuarios, clientes y tokens sin implementar identidad desde cero. |
| Autorización | ABAC, scopes detallados, RBAC | RBAC | Dos roles verificables: `admin` y `lector`. |
| Comunicación | REST/HTTP, MQTT, AMQP | REST/HTTP + JSON | Suficiente para el simulador y las APIs de la primera versión. |
| Persistencia | MySQL, MongoDB, PostgreSQL | PostgreSQL | Modelo relacional y consultas de telemetría, alertas y tickets. |
| Contenedores | Ejecución local, Docker Compose, Kubernetes | Docker Compose | Reproducibilidad multicontenedor sin complejidad de Kubernetes. |
| Pruebas API | Postman manual, pytest/HTTPX | pytest + HTTPX | Automatización de seguridad e integración. |
| Carga | JMeter, Locust, k6 | k6 | Escenarios legibles y métricas de carga. |
| Métricas | Administrador de tareas, Docker stats, Prometheus | Docker stats + logs inicialmente | Evidencia de CPU/RAM y diagnóstico; Prometheus es mejora futura. |
