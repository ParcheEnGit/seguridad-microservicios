from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TelemetryReadingCreate(BaseModel):
    device_id: UUID
    metric_code: str = Field(min_length=1, max_length=50)
    value: Decimal = Field(allow_inf_nan=False, max_digits=12, decimal_places=4)
    unit: str = Field(min_length=1, max_length=20)
    equipment_status: str | None = Field(default=None, max_length=30)
    recorded_at: datetime | None = None

    @field_validator("metric_code", "unit")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("El valor no puede estar vacío")
        return normalized


class TelemetryReadingResponse(BaseModel):
    id: UUID
    device_id: UUID
    metric_code: str
    value: Decimal
    unit: str
    equipment_status: str | None
    source: str
    recorded_at: datetime
    received_at: datetime


class SimulationMetric(BaseModel):
    metric_code: str
    unit: str
    min_value: float | None = None
    max_value: float | None = None

class TelemetryHistoryResponse(BaseModel):
    items: list[TelemetryReadingResponse]
    total: int
    limit: int
    offset: int

class SimulationTarget(BaseModel):
    device_id: UUID
    device_code: str
    needs_history: bool = False
    metrics: list[SimulationMetric]
