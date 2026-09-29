from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import SimulationMetric, SimulationTarget, TelemetryReadingCreate, TelemetryReadingResponse
from app.security import require_simulator_key

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
    SELECT d.id AS device_id, d.device_code, t.metric_code, t.unit,
           t.min_value::float, t.max_value::float
    FROM device_service.devices d
    LEFT JOIN device_service.thresholds t ON t.device_id = d.id
    WHERE d.status = 'activo'
    ORDER BY d.device_code, t.metric_code
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
            targets[key] = SimulationTarget(device_id=row["device_id"], device_code=row["device_code"], metrics=[])
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
