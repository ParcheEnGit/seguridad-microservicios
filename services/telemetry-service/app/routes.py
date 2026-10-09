from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    SimulationMetric,
    SimulationPeak,
    SimulationPeakCreate,
    SimulationTarget,
    TelemetryHistoryResponse,
    TelemetryReadingCreate,
    TelemetryReadingIngestResponse,
    TelemetryReadingResponse,
)
from app.security import get_current_claims, require_admin, require_simulator_key

router = APIRouter(tags=["telemetría"])

READING_ERROR_RESPONSES = {
    401: {"description": "Falta la cabecera X-Simulator-Key o no es válida"},
    404: {"description": "El dispositivo no existe"},
    409: {"description": "El dispositivo no está activo"},
    422: {"description": "Datos inválidos o unidad distinta a la del umbral configurado"},
}

HISTORY_ERROR_RESPONSES = {
    401: {"description": "Sesión ausente, inválida o expirada"},
    422: {"description": "Parámetros inválidos o fecha inicial posterior a la final"},
}

DEFAULT_METRICS = (
    SimulationMetric(metric_code="temperatura", unit="°c", min_value=18, max_value=28),
    SimulationMetric(metric_code="humedad", unit="%", min_value=40, max_value=70),
)
SIMULATION_PEAKS: dict[UUID, dict] = {}
SIMULATION_PEAKS_LOCK = Lock()

DEVICE_SQL = text("""
    SELECT id, status
    FROM device_service.devices
    WHERE id = :device_id
""")

THRESHOLD_SQL = text("""
    SELECT unit, min_value, max_value
    FROM device_service.thresholds
    WHERE device_id = :device_id AND metric_code = :metric_code
""")

PEAK_TARGET_SQL = text("""
    SELECT d.id, d.device_code, d.status, t.metric_code, t.unit,
           t.min_value::float AS min_value, t.max_value::float AS max_value
    FROM device_service.devices d
    JOIN device_service.thresholds t ON t.device_id = d.id
    WHERE d.id = :device_id AND t.metric_code = :metric_code
""")

INSERT_READING_SQL = text("""
    INSERT INTO telemetry_service.readings
        (device_id, metric_code, value, unit, equipment_status, source, recorded_at, payload)
    VALUES
        (:device_id, :metric_code, :value, :unit, :equipment_status, 'simulador', :recorded_at, '{}'::jsonb)
    RETURNING id, device_id, metric_code, value, unit, equipment_status, source, recorded_at, received_at
""")

INSERT_ALERT_SQL = text("""
    INSERT INTO alert_ticket_service.alerts (
        device_id, reading_id, metric_code, value, unit,
        threshold_min, threshold_max, severity
    )
    VALUES (
        :device_id, :reading_id, :metric_code, :value, :unit,
        :threshold_min, :threshold_max, :severity
    )
    ON CONFLICT (device_id, metric_code)
        WHERE status IN ('abierta', 'revisada')
    DO NOTHING
    RETURNING id
""")

TARGETS_SQL = text("""
    SELECT d.id AS device_id, d.device_code,
           NOT EXISTS (
               SELECT 1 FROM telemetry_service.readings r
               WHERE r.device_id = d.id
                 AND r.recorded_at BETWEEN NOW() - INTERVAL '7 days' AND NOW() - INTERVAL '6 hours'
           ) AS needs_history,
           t.metric_code, t.unit,
           t.min_value::float, t.max_value::float
    FROM device_service.devices d
    LEFT JOIN device_service.thresholds t ON t.device_id = d.id
    WHERE d.status = 'activo'
    ORDER BY d.device_code, t.metric_code
""")
HISTORY_SQL = text("""
    SELECT id, device_id, metric_code, value, unit,
           equipment_status, source, recorded_at, received_at
    FROM telemetry_service.readings
    WHERE device_id = :device_id
      AND (:metric_code IS NULL OR metric_code = :metric_code)
      AND recorded_at >= :start_at
      AND recorded_at <= :end_at
    ORDER BY recorded_at DESC
    LIMIT :limit OFFSET :offset
""")

HISTORY_COUNT_SQL = text("""
    SELECT COUNT(*)
    FROM telemetry_service.readings
    WHERE device_id = :device_id
      AND (:metric_code IS NULL OR metric_code = :metric_code)
      AND recorded_at >= :start_at
      AND recorded_at <= :end_at
""")


def normalize_recorded_at(value: datetime | None) -> datetime:
    timestamp = value or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def classify_threshold_breach(
    value: Decimal,
    min_value: Decimal,
    max_value: Decimal,
) -> tuple[str, str] | None:
    allowed_range = max_value - min_value
    if value < min_value:
        condition = "below_min"
        deviation = min_value - value
    elif value > max_value:
        condition = "above_max"
        deviation = value - max_value
    else:
        return None

    severity = (
        "critica"
        if deviation >= allowed_range * Decimal("0.10")
        else "advertencia"
    )
    return condition, severity


@router.post(
    "/readings",
    response_model=TelemetryReadingIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una lectura enviada por el simulador autorizado",
    responses=READING_ERROR_RESPONSES,
)
def create_reading(
    payload: TelemetryReadingCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_simulator_key),
) -> dict:
    device = db.execute(DEVICE_SQL, {"device_id": payload.device_id}).mappings().one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El dispositivo no existe")
    if device["status"] != "activo":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El dispositivo no está activo para recibir lecturas")

    threshold = db.execute(
        THRESHOLD_SQL,
        {"device_id": payload.device_id, "metric_code": payload.metric_code},
    ).mappings().one_or_none()
    if threshold is not None and threshold["unit"].strip().lower() != payload.unit:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La unidad no coincide con el umbral configurado")

    row = db.execute(
        INSERT_READING_SQL,
        {
            "device_id": payload.device_id,
            "metric_code": payload.metric_code,
            "value": payload.value,
            "unit": payload.unit,
            "equipment_status": payload.equipment_status,
            "recorded_at": normalize_recorded_at(payload.recorded_at),
        },
    ).mappings().one()

    alert_id = None
    alert_created = False
    condition = None
    severity = None
    if threshold is not None:
        anomaly = classify_threshold_breach(
            payload.value,
            threshold["min_value"],
            threshold["max_value"],
        )
        if anomaly is not None:
            condition, severity = anomaly
            inserted_alert = db.execute(
                INSERT_ALERT_SQL,
                {
                    "device_id": payload.device_id,
                    "reading_id": row["id"],
                    "metric_code": payload.metric_code,
                    "value": payload.value,
                    "unit": payload.unit,
                    "threshold_min": threshold["min_value"],
                    "threshold_max": threshold["max_value"],
                    "severity": severity,
                },
            ).mappings().one_or_none()
            alert_created = inserted_alert is not None

            if inserted_alert is not None:
                alert_id = inserted_alert["id"]
            else:
                existing_alert = db.execute(
                    text("""
                        SELECT id, severity
                        FROM alert_ticket_service.alerts
                        WHERE device_id = :device_id
                          AND metric_code = :metric_code
                          AND status IN ('abierta', 'revisada')
                    """),
                    {
                        "device_id": payload.device_id,
                        "metric_code": payload.metric_code,
                    },
                ).mappings().one_or_none()
                if existing_alert is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="No se pudo confirmar la alerta activa; reintenta el envío",
                    )
                alert_id = existing_alert["id"]
                if severity == "critica" and existing_alert["severity"] != "critica":
                    db.execute(
                        text("""
                            UPDATE alert_ticket_service.alerts
                            SET severity = 'critica', updated_at = NOW()
                            WHERE id = :alert_id
                        """),
                        {"alert_id": alert_id},
                    )

    db.commit()
    return {
        **dict(row),
        "out_of_range": condition is not None,
        "condition": condition,
        "severity": severity,
        "alert_id": alert_id,
        "alert_created": alert_created,
    }

@router.get(
    "/simulation-targets",
    response_model=list[SimulationTarget],
    summary="Obtener dispositivos activos que deben recibir lecturas simuladas",
)
def simulation_targets(
    db: Session = Depends(get_db),
    _: None = Depends(require_simulator_key),
) -> list[SimulationTarget]:
    targets: dict[str, SimulationTarget] = {}
    for row in db.execute(TARGETS_SQL).mappings():
        key = str(row["device_id"])
        if key not in targets:
            targets[key] = SimulationTarget(
                device_id=row["device_id"],
                device_code=row["device_code"],
                needs_history=row["needs_history"],
                metrics=[],
            )
        if row["metric_code"]:
            targets[key].metrics.append(
                SimulationMetric(
                    metric_code=row["metric_code"],
                    unit=row["unit"].strip().lower(),
                    min_value=row["min_value"],
                    max_value=row["max_value"],
                )
            )

    for target in targets.values():
        existing = {metric.metric_code for metric in target.metrics}
        target.metrics.extend(metric for metric in DEFAULT_METRICS if metric.metric_code not in existing)
    return list(targets.values())


@router.post(
    "/simulation/peaks",
    response_model=SimulationPeak,
    status_code=status.HTTP_201_CREATED,
    summary="Programar un pico demostrativo para el simulador",
)
def create_simulation_peak(
    payload: SimulationPeakCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    target = db.execute(
        PEAK_TARGET_SQL,
        {"device_id": payload.device_id, "metric_code": payload.metric_code},
    ).mappings().one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El dispositivo no tiene un umbral para esa métrica")
    if target["status"] != "activo":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El dispositivo debe estar activo para simular un pico")

    range_size = target["max_value"] - target["min_value"]
    margin = max(range_size * 0.25, 0.5)
    value = target["max_value"] + margin if payload.direction == "alto" else target["min_value"] - margin
    peak = {
        "id": uuid4(),
        "device_id": target["id"],
        "device_code": target["device_code"],
        "metric_code": target["metric_code"],
        "unit": target["unit"].strip().lower(),
        "value": round(value, 2),
        "cycles_remaining": payload.cycles,
        "created_at": datetime.now(timezone.utc),
    }
    with SIMULATION_PEAKS_LOCK:
        SIMULATION_PEAKS[peak["id"]] = peak
    return peak


@router.get(
    "/simulation/peaks",
    response_model=list[SimulationPeak],
    summary="Obtener picos demostrativos pendientes",
)
def list_simulation_peaks(_: None = Depends(require_simulator_key)) -> list[dict]:
    with SIMULATION_PEAKS_LOCK:
        return list(SIMULATION_PEAKS.values())


@router.post(
    "/simulation/peaks/{peak_id}/consume",
    summary="Consumir un ciclo de un pico demostrativo",
)
def consume_simulation_peak(peak_id: UUID, _: None = Depends(require_simulator_key)) -> dict:
    with SIMULATION_PEAKS_LOCK:
        peak = SIMULATION_PEAKS.get(peak_id)
        if peak is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El pico ya no está disponible")
        peak["cycles_remaining"] -= 1
        remaining = peak["cycles_remaining"]
        if remaining <= 0:
            del SIMULATION_PEAKS[peak_id]
    return {"consumed": True, "cycles_remaining": max(remaining, 0)}

@router.get(
    "/readings/history",
    response_model=TelemetryHistoryResponse,
    summary="Consultar historial de lecturas",
    description="Devuelve las lecturas del dispositivo ordenadas de la más reciente a la más antigua.",
    responses=HISTORY_ERROR_RESPONSES,
)
def reading_history(
    device_id: UUID = Query(...),
    start_at: datetime = Query(...),
    end_at: datetime = Query(...),
    metric_code: str | None = Query(default=None, min_length=1, max_length=50),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_claims),
) -> TelemetryHistoryResponse:
    if start_at > end_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha inicial no puede ser posterior a la fecha final",
        )

    history_params = {
        "device_id": device_id,
        "metric_code": metric_code.strip().lower() if metric_code else None,
        "start_at": start_at,
        "end_at": end_at,
    }

    total = db.execute(
        HISTORY_COUNT_SQL,
        history_params,
    ).scalar_one()

    rows = db.execute(
        HISTORY_SQL,
        {
            **history_params,
            "limit": limit,
            "offset": offset,
        },
    ).mappings().all()

    return TelemetryHistoryResponse(
        items=[TelemetryReadingResponse(**row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
