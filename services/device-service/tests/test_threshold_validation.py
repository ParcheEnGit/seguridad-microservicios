"""Contrato de métricas y unidades válidas para umbrales."""
import pytest
from pydantic import ValidationError

from app.schemas import ThresholdInput


@pytest.mark.parametrize(
    "metric_code,unit",
    [
        ("temperatura", "°C"),
        ("temperatura", "°F"),
        ("humedad", "%"),
        ("co2", "ppm"),
        ("presion", "hPa"),
    ],
)
def test_admite_unidades_estandar(metric_code, unit):
    threshold = ThresholdInput(
        metric_code=metric_code,
        unit=unit,
        min_value=1,
        max_value=2,
    )
    assert threshold.unit == unit


@pytest.mark.parametrize(
    "metric_code,unit",
    [
        ("temperatura", "XD"),
        ("humedad", "°C"),
        ("medicion_inventada", "%"),
    ],
)
def test_rechaza_metricas_y_unidades_no_normalizadas(metric_code, unit):
    with pytest.raises(ValidationError):
        ThresholdInput(
            metric_code=metric_code,
            unit=unit,
            min_value=1,
            max_value=2,
        )
