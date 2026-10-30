-- Normaliza representaciones usadas antes de que el catálogo de unidades se
-- validara en la API. Es segura de ejecutar varias veces.
UPDATE device_service.thresholds
SET unit = '%'
WHERE metric_code = 'humedad'
  AND lower(trim(unit)) IN ('porcentaje', 'percent', 'percentage');

UPDATE device_service.thresholds
SET unit = '°C'
WHERE metric_code = 'temperatura'
  AND lower(trim(unit)) IN ('c', '°c', 'celsius', 'centigrados', 'xd', 'grados', 'degrees');

-- Cualquier otra unidad no canónica de temperatura queda en °C para que el
-- modal de umbrales pueda guardarse sin chocar con ThresholdInput.
UPDATE device_service.thresholds
SET unit = '°C'
WHERE metric_code = 'temperatura'
  AND unit NOT IN ('°C', '°F');

UPDATE device_service.thresholds
SET unit = '%'
WHERE metric_code = 'humedad'
  AND unit <> '%';
