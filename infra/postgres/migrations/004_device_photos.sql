-- Fotografías asociadas a dispositivos. El archivo vive en el volumen del device-service;
-- PostgreSQL conserva únicamente metadatos y la ruta pública de cada imagen.
CREATE TABLE IF NOT EXISTS device_service.device_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES device_service.devices(id) ON DELETE CASCADE,
    storage_name VARCHAR(160) NOT NULL UNIQUE,
    original_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(80) NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_device_photo_size CHECK (size_bytes > 0 AND size_bytes <= 5242880),
    CONSTRAINT chk_device_photo_type CHECK (content_type IN ('image/jpeg', 'image/png', 'image/webp'))
);

CREATE INDEX IF NOT EXISTS idx_device_photos_device_created
    ON device_service.device_photos(device_id, created_at);
