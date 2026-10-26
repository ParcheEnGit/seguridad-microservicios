import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_STATUSES = {"activo", "inactivo", "mantenimiento"}

# Catálogo pequeño y explícito para evitar que la configuración de umbrales
# termine almacenando unidades ambiguas o inventadas (por ejemplo, "XD").
# Las métricas soportadas hoy por el simulador y los dashboards están incluidas,
# junto a magnitudes técnicas habituales para los dispositivos de laboratorio.
ALLOWED_UNITS_BY_METRIC = {
    "temperatura": {"°C", "°F"},
    "humedad": {"%"},
    "co2": {"ppm"},
    "calidad_aire": {"ppm"},
    "presion": {"Pa", "hPa", "kPa"},
    "voltaje": {"mV", "V"},
    "corriente": {"mA", "A"},
    "potencia": {"W", "kW"},
    "iluminacion": {"lx"},
}


class ThresholdInput(BaseModel):
    metric_code: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    unit: str = Field(min_length=1, max_length=20)
    min_value: float
    max_value: float

    @field_validator("metric_code")
    @classmethod
    def metric_is_supported(cls, value: str) -> str:
        metric_code = value.strip().lower()
        if metric_code not in ALLOWED_UNITS_BY_METRIC:
            raise ValueError("Métrica no admitida para umbrales")
        return metric_code

    @field_validator("unit")
    @classmethod
    def unit_matches_metric(cls, value: str, info) -> str:
        unit = value.strip()
        metric_code = info.data.get("metric_code")
        if metric_code and unit not in ALLOWED_UNITS_BY_METRIC[metric_code]:
            allowed_units = ", ".join(sorted(ALLOWED_UNITS_BY_METRIC[metric_code]))
            raise ValueError(f"Unidad no válida para {metric_code}. Usa: {allowed_units}")
        return unit

    @field_validator("max_value")
    @classmethod
    def range_is_valid(cls, value: float, info) -> float:
        if "min_value" in info.data and value <= info.data["min_value"]:
            raise ValueError("max_value debe ser mayor que min_value")
        return value


class DeviceCreate(BaseModel):
    device_code: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    device_type: str = Field(min_length=2, max_length=60)
    location: str = Field(min_length=2, max_length=120)
    status: str = "activo"
    metadata: dict = Field(default_factory=dict)
    thresholds: list[ThresholdInput] = Field(default_factory=list, max_length=20)

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in ALLOWED_STATUSES:
            raise ValueError("Estado no válido")
        return value


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    device_type: str | None = Field(default=None, min_length=2, max_length=60)
    location: str | None = Field(default=None, min_length=2, max_length=120)
    status: str | None = None
    metadata: dict | None = None

    @field_validator("status")
    @classmethod
    def valid_optional_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_STATUSES:
            raise ValueError("Estado no válido")
        return value


class ThresholdResponse(BaseModel):
    """Representación persistida.

    La validación estricta de unidades pertenece a ``ThresholdInput`` (datos
    nuevos). La respuesta no debe convertir un valor legado en un 500 mientras
    la migración de normalización se ejecuta.
    """
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    device_id: uuid.UUID
    metric_code: str
    unit: str
    min_value: float
    max_value: float
    created_at: datetime
    updated_at: datetime


class DevicePhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime
    url: str


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: uuid.UUID
    device_code: str
    name: str
    device_type: str
    location: str
    status: str
    metadata: dict = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    thresholds: list[ThresholdResponse] = []
    photos: list[DevicePhotoResponse] = []


class DeviceListResponse(BaseModel):
    items: list[DeviceResponse]
    total: int


class DeviceStatusUpdate(BaseModel):
    status: str = "inactivo"

    @field_validator("status")
    @classmethod
    def only_inactive(cls, value: str) -> str:
        if value != "inactivo":
            raise ValueError("La desactivación solo admite el estado inactivo")
        return value
