"""Endpoints del report-service para el Dashboard Admin (HU4).

El report-service es el servicio de CONSULTA de LabSentinel: consolida información
de los demás servicios para mostrarla. Por eso solo ejecuta SELECT de solo lectura
sobre los esquemas device_service, telemetry_service y alert_ticket_service.
Nunca inserta, actualiza ni borra datos que pertenecen a otros servicios.
"""
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AdminSummary, DeviceTelemetrySeries
from app.security import get_current_claims, require_admin

from app.report_queries import (
    DEVICE_REPORT_SUMMARY_SQL,
    DEVICE_REPORT_DETAILS_SQL,
    DEVICE_REPORT_TIMELINE_SQL,
    ALERT_REPORT_SUMMARY_SQL,
    ALERT_REPORT_DETAILS_SQL,
    ALERT_REPORT_TIMELINE_SQL,
    TICKET_REPORT_SUMMARY_SQL,
    TICKET_REPORT_DETAILS_SQL,
    TICKET_REPORT_TIMELINE_SQL,
)

from app.schemas import (
    DeviceReportResponse,
    AlertReportResponse,
    TicketReportResponse,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])

RECENT_ALERTS_LIMIT = 3


# HU11: Validar fechas de los reportes administrativos.
def validate_report_dates(start_date: date, end_date: date) -> None:
    today = datetime.now(timezone.utc).date()

    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha inicial no puede ser posterior a la fecha final",
        )

    if start_date > today or end_date > today:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se permiten fechas futuras en los reportes",
        )


DEVICE_COUNTS_SQL = text("""
    SELECT COUNT(*)                                         AS total,
           COUNT(*) FILTER (WHERE status = 'activo')        AS activo,
           COUNT(*) FILTER (WHERE status = 'inactivo')      AS inactivo,
           COUNT(*) FILTER (WHERE status = 'mantenimiento') AS mantenimiento
    FROM device_service.devices
""")

ALERT_COUNTS_SQL = text("""
    SELECT COUNT(*) FILTER (WHERE status IN ('abierta', 'revisada'))                         AS active,
           COUNT(*) FILTER (WHERE status = 'abierta')                                        AS pending_review,
           COUNT(*) FILTER (WHERE status IN ('abierta', 'revisada') AND severity = 'critica') AS critical
    FROM alert_ticket_service.alerts
""")

TICKET_COUNTS_SQL = text("""
    SELECT COUNT(*) FILTER (WHERE status IN ('abierto', 'en_revision'))         AS open,
           COUNT(*) FILTER (WHERE created_at >= date_trunc('day', NOW()))       AS created_today
    FROM alert_ticket_service.tickets
""")

READING_STATS_SQL = text("""
    SELECT COUNT(*) FILTER (WHERE recorded_at >= date_trunc('day', NOW())) AS today,
           MAX(received_at)                                                AS last_received_at
    FROM telemetry_service.readings
""")

RECENT_ALERTS_SQL = text("""
    SELECT a.id, d.name AS device_name, d.device_code, a.metric_code, a.value, a.unit,
           a.threshold_min, a.threshold_max, a.severity, a.status, a.created_at
    FROM alert_ticket_service.alerts a
    LEFT JOIN device_service.devices d ON d.id = a.device_id
    WHERE a.status IN ('abierta', 'revisada')
    ORDER BY a.created_at DESC
    LIMIT :limit
""")

CHART_24H_SQL = text("""
    -- Un minuto conserva la evolución ambiental de un simulador que emite
    -- cada pocos segundos, sin acercarse al volumen de las lecturas crudas.
    SELECT date_bin(INTERVAL '1 minute', r.recorded_at, TIMESTAMPTZ '2000-01-01') AS hour,
           AVG(r.value) FILTER (WHERE r.metric_code = 'temperatura')::float       AS temperatura,
           AVG(r.value) FILTER (WHERE r.metric_code = 'humedad')::float           AS humedad,
           COALESCE(BOOL_OR(r.value < t.min_value OR r.value > t.max_value)
               FILTER (WHERE r.metric_code = 'temperatura'), FALSE)               AS temperatura_out_of_range,
           COALESCE(BOOL_OR(r.value < t.min_value OR r.value > t.max_value)
               FILTER (WHERE r.metric_code = 'humedad'), FALSE)                   AS humedad_out_of_range
    FROM telemetry_service.readings r
    JOIN device_service.devices d ON d.id = r.device_id
    LEFT JOIN device_service.thresholds t
        ON t.device_id = r.device_id AND t.metric_code = r.metric_code
    WHERE r.recorded_at >= NOW() - INTERVAL '24 hours'
      AND r.metric_code IN ('temperatura', 'humedad')
      AND concat_ws(' ', d.name, d.device_code, d.device_type) ILIKE '%ambient%'
      -- No mezclar rellenos históricos del simulador con las mediciones del
      -- ciclo actual: se reciben mucho después de su recorded_at y dibujan
      -- diagonales artificiales al reiniciar el entorno.
      AND (
          r.source IS DISTINCT FROM 'simulador'
          OR r.received_at - r.recorded_at <= INTERVAL '5 minutes'
      )
    GROUP BY 1
    ORDER BY 1
""")

SERIES_OPTIONS = {
    "1h": ("1 hour", "15 seconds"),
    "6h": ("6 hours", "1 minute"),
    "24h": ("24 hours", "5 minutes"),
    "7d": ("7 days", "1 hour"),
    "30d": ("30 days", "1 day"),
}

RESOLUTION_OPTIONS = {"15s": "15 seconds", "1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes", "1h": "1 hour", "1d": "1 day"}

SERIES_DEVICES_SQL = text("""
    SELECT id, name, device_code
    FROM device_service.devices
    WHERE status = 'activo'
    ORDER BY name
""")

DEVICE_SERIES_SQL = text("""
    SELECT date_bin(CAST(:bucket AS interval), r.recorded_at, TIMESTAMPTZ '2000-01-01') AS bucket,
           r.device_id, r.metric_code, AVG(r.value)::float AS value,
           COALESCE(BOOL_OR(r.value < t.min_value OR r.value > t.max_value), FALSE) AS out_of_range,
           COALESCE(BOOL_OR((r.payload ->> 'simulation_event') IN ('pico_forzado', 'pico_aleatorio')), FALSE) AS simulated_peak
    FROM telemetry_service.readings r
    JOIN device_service.devices d ON d.id = r.device_id AND d.status = 'activo'
    LEFT JOIN device_service.thresholds t
        ON t.device_id = r.device_id AND t.metric_code = r.metric_code
    WHERE r.recorded_at >= NOW() - CAST(:period AS interval)
      AND r.metric_code IN ('temperatura', 'humedad')
      -- No se muestran rellenos históricos antiguos del simulador. Fueron
      -- recibidos mucho después de su timestamp y no representan mediciones
      -- continuas; conservarlos visualmente creaba diagonales engañosas.
      AND (
          r.source IS DISTINCT FROM 'simulador'
          OR r.received_at - r.recorded_at <= INTERVAL '5 minutes'
      )
    GROUP BY 1, r.device_id, r.metric_code
    ORDER BY 1, r.device_id, r.metric_code
""")


@router.get("/admin-summary", response_model=AdminSummary, summary="Resumen operativo del Dashboard Admin")
def admin_summary(db: Session = Depends(get_db), _: dict = Depends(require_admin)) -> AdminSummary:
    return AdminSummary(
        devices=dict(db.execute(DEVICE_COUNTS_SQL).mappings().one()),
        alerts=dict(db.execute(ALERT_COUNTS_SQL).mappings().one()),
        tickets=dict(db.execute(TICKET_COUNTS_SQL).mappings().one()),
        readings=dict(db.execute(READING_STATS_SQL).mappings().one()),
        recent_alerts=[dict(row) for row in db.execute(RECENT_ALERTS_SQL, {"limit": RECENT_ALERTS_LIMIT}).mappings()],
        chart_24h=[dict(row) for row in db.execute(CHART_24H_SQL).mappings()],
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/telemetry-summary", response_model=AdminSummary, summary="Resumen de telemetría para dashboards autorizados")
def telemetry_summary(db: Session = Depends(get_db), _: dict = Depends(get_current_claims)) -> AdminSummary:
    return AdminSummary(
        devices=dict(db.execute(DEVICE_COUNTS_SQL).mappings().one()),
        alerts=dict(db.execute(ALERT_COUNTS_SQL).mappings().one()),
        tickets=dict(db.execute(TICKET_COUNTS_SQL).mappings().one()),
        readings=dict(db.execute(READING_STATS_SQL).mappings().one()),
        recent_alerts=[],
        chart_24h=[dict(row) for row in db.execute(CHART_24H_SQL).mappings()],
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/device-telemetry", response_model=DeviceTelemetrySeries, summary="Consultar telemetría agregada por dispositivo")
def device_telemetry(
    period: str = Query(default="24h"),
    resolution: str = Query(default="5m"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_claims),
) -> DeviceTelemetrySeries:
    if period not in SERIES_OPTIONS or resolution not in RESOLUTION_OPTIONS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Periodo o resolución no permitidos")
    period_interval, default_bucket = SERIES_OPTIONS[period]
    bucket = RESOLUTION_OPTIONS[resolution]
    # Evita consultas excesivas: para periodos largos se conserva una granularidad mínima razonable.
    if period == "7d" and resolution in {"15s", "1m", "5m"}:
        bucket = default_bucket
    if period == "30d" and resolution != "1d":
        bucket = default_bucket
    return DeviceTelemetrySeries(
        devices=[dict(row) for row in db.execute(SERIES_DEVICES_SQL).mappings()],
        points=[dict(row) for row in db.execute(DEVICE_SERIES_SQL, {"period": period_interval, "bucket": bucket}).mappings()],
        period=period,
        resolution=next(key for key, value in RESOLUTION_OPTIONS.items() if value == bucket),
    )

# HU11: Reporte administrativo de dispositivos.
@router.get(
    "/reports/devices",
    response_model=DeviceReportResponse,
    summary="Generar reporte de dispositivos por período",
)
def devices_report(
    start_date: date = Query(..., description="Fecha inicial (AAAA-MM-DD)"),
    end_date: date = Query(..., description="Fecha final (AAAA-MM-DD)"),
    device_id: UUID | None = Query(default=None),
    device_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> DeviceReportResponse:
    validate_report_dates(start_date, end_date)

    if device_status not in (None, "activo", "inactivo", "mantenimiento"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El estado del dispositivo no es válido",
        )

    # Se incluye el día final completo mediante un límite superior exclusivo.
    start_datetime = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc,
    )

    params = {
        "start_date": start_datetime,
        "end_date": end_datetime,
        "device_id": str(device_id) if device_id else None,
        "device_status": device_status,
    }

    summary = dict(db.execute(DEVICE_REPORT_SUMMARY_SQL, params).mappings().one())

    devices = [
        dict(row)
        for row in db.execute(DEVICE_REPORT_DETAILS_SQL, params).mappings()
    ]

    timeline = [
        dict(row)
        for row in db.execute(DEVICE_REPORT_TIMELINE_SQL, params).mappings()
    ]

    return DeviceReportResponse(
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        devices=devices,
        timeline=timeline,
        generated_at=datetime.now(timezone.utc),
    )



# HU11: Reporte administrativo de alertas.
@router.get(
    "/reports/alerts",
    response_model=AlertReportResponse,
    summary="Generar reporte de alertas por período",
)
def alerts_report(
    start_date: date = Query(..., description="Fecha inicial (AAAA-MM-DD)"),
    end_date: date = Query(..., description="Fecha final (AAAA-MM-DD)"),
    device_id: UUID | None = Query(default=None),
    severity: str | None = Query(default=None),
    alert_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> AlertReportResponse:
    validate_report_dates(start_date, end_date)

    if severity not in (None, "advertencia", "critica"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La severidad de la alerta no es válida",
        )

    if alert_status not in (None, "abierta", "revisada", "cerrada"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El estado de la alerta no es válido",
        )

    start_datetime = datetime.combine(
        start_date,
        time.min,
        tzinfo=timezone.utc,
    )
    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc,
    )

    params = {
        "start_date": start_datetime,
        "end_date": end_datetime,
        "device_id": str(device_id) if device_id else None,
        "severity": severity,
        "alert_status": alert_status,
    }

    summary = dict(
        db.execute(ALERT_REPORT_SUMMARY_SQL, params).mappings().one()
    )

    alerts = [
        dict(row)
        for row in db.execute(ALERT_REPORT_DETAILS_SQL, params).mappings()
    ]

    timeline = [
        dict(row)
        for row in db.execute(ALERT_REPORT_TIMELINE_SQL, params).mappings()
    ]

    return AlertReportResponse(
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        alerts=alerts,
        timeline=timeline,
        generated_at=datetime.now(timezone.utc),
    )



# HU11: Reporte administrativo de tickets.
@router.get(
    "/reports/tickets",
    response_model=TicketReportResponse,
    summary="Generar reporte de tickets por período",
)
def tickets_report(
    start_date: date = Query(..., description="Fecha inicial (AAAA-MM-DD)"),
    end_date: date = Query(..., description="Fecha final (AAAA-MM-DD)"),
    device_id: UUID | None = Query(default=None),
    ticket_status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> TicketReportResponse:
    validate_report_dates(start_date, end_date)

    if ticket_status not in (
        None,
        "abierto",
        "en_revision",
        "resuelto",
        "cerrado",
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El estado del ticket no es válido",
        )

    if category not in (
        None,
        "carcasa_rota",
        "tapa_faltante",
        "etiqueta_ilegible",
        "deterioro_estetico",
        "otro",
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La categoría del ticket no es válida",
        )

    start_datetime = datetime.combine(
        start_date,
        time.min,
        tzinfo=timezone.utc,
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc,
    )

    params = {
        "start_date": start_datetime,
        "end_date": end_datetime,
        "device_id": str(device_id) if device_id else None,
        "ticket_status": ticket_status,
        "category": category,
    }

    summary = dict(
        db.execute(TICKET_REPORT_SUMMARY_SQL, params).mappings().one()
    )

    tickets = [
        dict(row)
        for row in db.execute(TICKET_REPORT_DETAILS_SQL, params).mappings()
    ]

    timeline = [
        dict(row)
        for row in db.execute(TICKET_REPORT_TIMELINE_SQL, params).mappings()
    ]

    return TicketReportResponse(
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        tickets=tickets,
        timeline=timeline,
        generated_at=datetime.now(timezone.utc),
    )
