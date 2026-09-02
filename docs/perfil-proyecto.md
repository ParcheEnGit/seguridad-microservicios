# Perfil del proyecto

## 1. Título provisional

**Diseño e implementación de mecanismos de autenticación y autorización para la protección de recursos en una arquitectura de microservicios telemáticos.**

El título es provisional y deberá actualizarse cuando se seleccione la tecnología; así cumplirá plenamente la fórmula “qué se desarrollará + tecnología/ámbito + finalidad + contexto”.

## 2. Línea temática

Seguridad, microservicios, servicios distribuidos y contenedores (si se adopta Docker).

## 3. Descripción general

Los sistemas distribuidos compuestos por microservicios exponen múltiples puntos de acceso y, sin un control homogéneo de identidad y permisos, pueden entregar recursos a usuarios no autorizados. El proyecto construirá un prototipo con un punto de entrada, un servicio de identidad y un servicio de recurso protegido. Un cliente se autenticará, recibirá una credencial y solo podrá acceder a las operaciones permitidas por su rol o permiso.

El recurso protegido será deliberadamente pequeño y representativo —por ejemplo, consulta de documentos o información académica de prueba—, porque el objeto de evaluación es la seguridad entre servicios y no un sistema de gestión completo.

## 4. Problema inicial

¿Cómo diseñar e implementar mecanismos de autenticación y autorización en una arquitectura de microservicios que permitan controlar de forma verificable el acceso a un recurso telemático protegido?

## 5. Objetivo general

Diseñar e implementar una arquitectura de microservicios con mecanismos de autenticación y autorización para proteger el acceso a recursos telemáticos y evaluar su funcionamiento mediante pruebas de seguridad y rendimiento.

## 6. Objetivos específicos propuestos

1. Analizar los riesgos de acceso no autorizado y los mecanismos de seguridad aplicables a microservicios.
2. Definir los requisitos de acceso, roles, permisos y flujos de autenticación del prototipo.
3. Diseñar la arquitectura, comunicación y despliegue de los microservicios protegidos.
4. Seleccionar y justificar las tecnologías, protocolos y mecanismo de credenciales a utilizar.
5. Implementar los servicios y las políticas de autorización acordadas.
6. Evaluar el prototipo mediante pruebas funcionales, de seguridad, rendimiento y escalabilidad.

## 7. Alcance y entregables

El alcance funcional y los límites se definen en el README. Se entregarán: código fuente organizado, contratos de API, diagramas, configuración reproducible, plan y resultados de pruebas, informe, manual técnico y presentación/demostración.

## 8. Pendiente de completar

- Integrantes y responsabilidades.
- Cronograma con hitos y fechas.
- Contexto específico del recurso protegido.
- Matriz de justificación y costos.
- Referencias para marco teórico y estado del arte.
