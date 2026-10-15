"""Notificaciones salientes de alertas de telemetría.

Las credenciales SMTP nunca se guardan en código ni se devuelven a la API. Este
módulo se ejecuta como tarea de fondo después de confirmar la alerta en la BD.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from app.core.config import Settings

logger = logging.getLogger(__name__)


def configured_recipients(raw_recipients: str) -> set[str]:
    return {
        email.strip().lower()
        for email in raw_recipients.split(",")
        if email.strip()
    }


def send_alert_email(
    *,
    settings: Settings,
    recipients: set[str],
    device_name: str | None,
    device_code: str | None,
    metric_code: str,
    value: object,
    unit: str,
    threshold_min: object,
    threshold_max: object,
    condition: str,
    severity: str,
    event: str | None,
    device_photo_path: Path | None = None,
) -> None:
    """Envía un aviso TLS sin interrumpir el registro de telemetría."""
    if not settings.smtp_enabled or not recipients:
        return
    if not all((settings.smtp_host, settings.smtp_username, settings.smtp_from)):
        logger.warning("Correo de alertas omitido: la configuración SMTP está incompleta")
        return

    # Google muestra las contraseñas de aplicación agrupadas con espacios; SMTP
    # recibe el token continuo. También tolera proveedores que no las agrupan.
    password = "".join(settings.smtp_password.get_secret_value().split())
    if not password:
        logger.warning("Correo de alertas omitido: falta SMTP_PASSWORD")
        return

    device = device_name or device_code or "Dispositivo sin nombre"
    if device_code and device_code != device:
        device = f"{device} ({device_code})"
    direction = "superó el máximo" if condition == "above_max" else "bajó del mínimo"
    event_label = {
        "pico_forzado": "pico forzado de demostración",
        "pico_aleatorio": "pico aleatorio del simulador",
    }.get(event or "", "lectura fuera de umbral")

    content = (
        "LabSentinel detectó una condición anómala.\n\n"
        f"Dispositivo: {device}\n"
        f"Métrica: {metric_code}\n"
        f"Lectura: {value} {unit}\n"
        f"Umbral permitido: {threshold_min} a {threshold_max} {unit}\n"
        f"Condición: {direction}\n"
        f"Severidad: {severity}\n"
        f"Origen: {event_label}\n"
        f"Fotografía adjunta: {'sí' if device_photo_path and device_photo_path.is_file() else 'no disponible'}\n\n"
        "Ingresa al Dashboard Admin de LabSentinel para revisar y gestionar la alerta."
    )

    photo_content = None
    if device_photo_path and device_photo_path.is_file():
        try:
            photo_content = device_photo_path.read_bytes()
        except OSError as exc:
            # No se sacrifica la alerta por una fotografía que fue eliminada o no
            # está montada temporalmente en este servicio.
            logger.warning("No se pudo adjuntar la fotografía del dispositivo: %s", exc)

    delivered = 0
    failed = 0
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=12,
            context=context,
        ) as smtp:
            smtp.login(settings.smtp_username, password)
            for recipient in sorted(recipients):
                message = EmailMessage()
                message["Subject"] = f"[LabSentinel] Alerta {severity}: {device}"
                message["From"] = settings.smtp_from
                # Un mensaje por destinatario evita divulgar la lista de admins.
                message["To"] = recipient
                message.set_content(content)
                if photo_content:
                    message.add_attachment(
                        photo_content,
                        maintype="image",
                        subtype="webp",
                        filename=f"{device_code or 'dispositivo'}-alerta.webp",
                    )
                refused = smtp.send_message(message)
                if refused:
                    failed += 1
                    logger.warning("El proveedor SMTP rechazó el correo de alerta para %s", recipient)
                else:
                    delivered += 1
        logger.info("Correo de alerta enviado a %d administrador(es); %d rechazado(s)", delivered, failed)
    except (OSError, smtplib.SMTPException) as exc:
        # La telemetría y la alerta ya quedaron persistidas; un fallo de correo no
        # puede perder la evidencia ni detener el simulador.
        logger.error("No se pudo enviar el correo de alerta: %s", exc)
