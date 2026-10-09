CREATE OR REPLACE FUNCTION device_service.enforce_device_photo_limit()
RETURNS TRIGGER AS $$
BEGIN
    IF (
        SELECT COUNT(*)
        FROM device_service.device_photos
        WHERE device_id = NEW.device_id
    ) >= 3 THEN
        RAISE EXCEPTION 'Cada dispositivo admite como máximo 3 fotografías';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_device_photo_limit ON device_service.device_photos;
CREATE TRIGGER trg_device_photo_limit
BEFORE INSERT ON device_service.device_photos
FOR EACH ROW EXECUTE FUNCTION device_service.enforce_device_photo_limit();
