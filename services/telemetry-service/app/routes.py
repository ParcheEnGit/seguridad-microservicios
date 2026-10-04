from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    SimulationMetric,
    SimulationTarget,
    TelemetryHistoryResponse,
    TelemetryReadingCreate,
    TelemetryReadingResponse,
)
from app.security import get_current_claims, require_simulator_key

router = APIRouter(tags=["telemetría"])

DEFAULT_METRICS = (
    SimulationMetric(metric_code="temperatura", unit="°c", min_value=18, max_value=28),
    SimulationMetric(metric_code="humedad", unit="%", min_value=40, max_value=70),
)

DEVICE_SQL = text("""
    SELECT id, status
    FROM device_service.devices
    WHERE id = :device_id
""")

THRESHOLD_SQL = text("""
    SELECT unit
    FROM device_service.thresholds
    WHERE device_id = :device_id AND metric_code = :metric_code
""")

INSERT_READING_SQL = text("""
    INSERT INTO telemetry_service.readings
        (device_id, metric_code, value, unit, equipment_status, source, recorded_at, payload)
    VALUES
        (:device_id, :metric_code, :value, :unit, :equipment_status, 'simulador', :recorded_at, '{}'::jsonb)
    RETURNING id, device_id, metric_code, value, unit, equipment_status, source, recorded_at, received_at
""")

TARGETS_SQL = text("""
    SELECT d.id AS device_id, d.device_code,
           NOT EXISTS (
               SELECT 1 FROM telemetry_service.readings r
               WHERE r.device_id = d.id
                 AND r.recorded_at < NOW() - INTERVAL '6 hours'
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


@router.post(
    "/readings",
    response_model=TelemetryReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una lectura enviada por el simulador autorizado",
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

    threshold = db.execute(THRESHOLD_SQL, {"device_id": payload.device_id, "metric_code": payload.metric_code}).mappings().one_or_none()
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
    db.commit()
    return dict(row)

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

@router.get(
    "/readings/history",
    response_model=TelemetryHistoryResponse,
    summary="Consultar historial de lecturas",
)
def reading_history(
    device_id: str = Query(..., min_length=1),
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