from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DeviceCounts(BaseModel):
    total: int
    activo: int
    inactivo: int
    mantenimiento: int


class AlertCounts(BaseModel):
    active: int
    pending_review: int
    critical: int


class TicketCounts(BaseModel):
    open: int
    created_today: int


class ReadingStats(BaseModel):
    today: int
    last_received_at: datetime | None


class RecentAlert(BaseModel):
    id: UUID
    device_name: str | None
    device_code: str | None
    metric_code: str
    value: Decimal
    unit: str
    threshold_min: Decimal | None
    threshold_max: Decimal | None
    severity: str
    status: str
    created_at: datetime


class ChartPoint(BaseModel):
    hour: datetime
    temperatura: float | None
    humedad: float | None


class AdminSummary(BaseModel):
    devices: DeviceCounts
    alerts: AlertCounts
    tickets: TicketCounts
    readings: ReadingStats
    recent_alerts: list[RecentAlert]
    chart_24h: list[ChartPoint]
    generated_at: datetime
