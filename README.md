# Seguridad de microservicios — Grupo 36

Proyecto semestral de **Servicios Telemáticos**, gestión 2-2026.

## Propósito

Diseñar e implementar una arquitectura de microservicios que aplique autenticación y autorización para proteger el acceso a recursos de un servicio telemático. El producto será un conjunto reproducible de microservicios protegidos, acompañado de su documentación y pruebas experimentales.

> Estado inicial: la arquitectura lógica está definida, pero el grupo aún debe seleccionar y justificar el lenguaje, framework, proveedor de identidad, mecanismo de tokens, base de datos y observabilidad. No se debe considerar este repositorio como una implementación funcional todavía.

## Alcance inicial

- Autenticar usuarios y emitir credenciales de acceso.
- Autorizar solicitudes por roles o permisos.
- Proteger al menos un recurso expuesto por un microservicio.
- Centralizar el acceso externo mediante un API Gateway.
- Ejecutar pruebas funcionales, de seguridad, rendimiento y escalabilidad.
- Empaquetar la solución con contenedores si esa alternativa es aprobada por el grupo.

No incluye, salvo decisión posterior del grupo, gestión completa de usuarios, inicio de sesión social, recuperación de contraseñas, multi-tenencia, alta disponibilidad productiva ni despliegue cloud.

## Arquitectura lógica propuesta

```text
Cliente → API Gateway → Servicio de identidad
                     → Servicio de recurso protegido
```

El gateway recibe las solicitudes externas; el servicio de identidad autentica y entrega credenciales; y el recurso protegido valida la identidad/autorización antes de responder. Los nombres, protocolos concretos y tecnología se documentarán en [docs/arquitectura.md](docs/arquitectura.md).

## Estructura

```text
docs/          Perfil, arquitectura, decisiones y guías del informe
services/      Implementaciones independientes de cada microservicio
contracts/     Contratos de API compartidos, no código compartido
tests/         Pruebas funcionales, seguridad, rendimiento y escalabilidad
infra/         Contenedores, Compose, scripts y configuración de despliegue
```

## Próximos acuerdos del grupo

1. Definir el caso de uso del recurso protegido y los roles.
2. Comparar y seleccionar el stack tecnológico mediante la matriz en `docs/tecnologias.md`.
3. Decidir el mecanismo de autenticación/autorización (p. ej., JWT u OAuth 2.0/OIDC) y justificarlo.
4. Completar los contratos API y el diagrama de despliegue antes de programar.

## Trabajo colaborativo

- `main`: versiones estables y entregables.
- `develop`: integración del desarrollo.
- `feature/<tema>`: trabajo individual; por ejemplo, `feature/identity-service`.
- Abrir un pull request hacia `develop` y revisar antes de integrar.

## Documentación obligatoria

La guía del curso exige, entre otros componentes, perfil, problema, justificación, objetivos, marco teórico, estado del arte, arquitectura, selección de tecnologías, implementación, pruebas experimentales, análisis, manual técnico, presentación, código y documentación técnica. El índice y las plantillas están en [docs/README.md](docs/README.md).
