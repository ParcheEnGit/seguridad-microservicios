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
    temperatura_out_of_range: bool = False
    humedad_out_of_range: bool = False


class AdminSummary(BaseModel):
    devices: DeviceCounts
    alerts: AlertCounts
    tickets: TicketCounts
    readings: ReadingStats
    recent_alerts: list[RecentAlert]
    chart_24h: list[ChartPoint]
    generated_at: datetime


class TelemetryDevice(BaseModel):
    id: UUID
    name: str
    device_code: str


class DeviceTelemetryPoint(BaseModel):
    bucket: datetime
    device_id: UUID
    metric_code: str
    value: float
    out_of_range: bool = False
    simulated_peak: bool = False


class DeviceTelemetrySeries(BaseModel):
    devices: list[TelemetryDevice]
    points: list[DeviceTelemetryPoint]
    period: str
    resolution: str


# HU11: Esquemas para reportes administrativos de dispositivos.

from datetime import date


class DeviceReportSummary(BaseModel):
    total: int
    activos: int
    inactivos: int
    mantenimiento: int


class DeviceReportDetail(BaseModel):
    id: UUID
    device_code: str
    name: str
    device_type: str
    location: str
    status: str
    created_at: datetime


class DeviceReportTimelinePoint(BaseModel):
    day: date
    total: int


class DeviceReportResponse(BaseModel):
    start_date: date
    end_date: date
    summary: DeviceReportSummary
    timeline: list[DeviceReportTimelinePoint]
    devices: list[DeviceReportDetail]
    generated_at: datetime


# HU11: Esquemas para reportes administrativos de alertas.


class AlertReportSummary(BaseModel):
    total: int
    criticas: int
    advertencias: int
    abiertas: int
    revisadas: int
    cerradas: int


class AlertReportDetail(BaseModel):
    id: UUID
    device_id: UUID
    device_code: str | None = None
    device_name: str | None = None
    metric_code: str
    value: Decimal
    unit: str
    severity: str
    status: str
    created_at: datetime
    reviewed_at: datetime | None = None
    resolved_at: datetime | None = None


class AlertReportTimelinePoint(BaseModel):
    day: date
    total: int
    criticas: int
    advertencias: int


class AlertReportResponse(BaseModel):
    start_date: date
    end_date: date
    summary: AlertReportSummary
    timeline: list[AlertReportTimelinePoint]
    alerts: list[AlertReportDetail]
    generated_at: datetime
