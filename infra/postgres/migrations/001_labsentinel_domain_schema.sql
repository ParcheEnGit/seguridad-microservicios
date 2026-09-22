-- LabSentinel: esquema de dominio inicial.
-- Compatible con PostgreSQL 18 y seguro de ejecutar más de una vez.
-- public.users pertenece al auth-service existente; este archivo no la modifica.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SCHEMA IF NOT EXISTS device_service;
CREATE SCHEMA IF NOT EXISTS telemetry_service;
CREATE SCHEMA IF NOT EXISTS alert_ticket_service;
CREATE SCHEMA IF NOT EXISTS report_service;

-- DEVICE SERVICE: inventario y reglas de medición. Es propietario de estas tablas.
CREATE TABLE IF NOT EXISTS device_service.devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    device_type VARCHAR(60) NOT NULL,
    location VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'activo',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_devices_status CHECK (status IN ('activo', 'inactivo', 'mantenimiento'))
);

CREATE TABLE IF NOT EXISTS device_service.thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES device_service.devices(id) ON DELETE RESTRICT,
    metric_code VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    min_value NUMERIC(12, 4) NOT NULL,
    max_value NUMERIC(12, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_threshold_range CHECK (max_value > min_value),
    CONSTRAINT uq_threshold_device_metric UNIQUE (device_id, metric_code)
);

CREATE INDEX IF NOT EXISTS idx_thresholds_device ON device_service.thresholds(device_id);

-- TELEMETRY SERVICE: hechos inmutables. device_id es una referencia lógica;
-- no hay FK entre servicios para preservar la autonomía de cada servicio.
CREATE TABLE IF NOT EXISTS telemetry_service.readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    metric_code VARCHAR(50) NOT NULL,
    value NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    equipment_status VARCHAR(30),
    source VARCHAR(30) NOT NULL DEFAULT 'simulador',
    recorded_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT chk_readings_source CHECK (source IN ('simulador', 'dispositivo', 'manual'))
);

CREATE INDEX IF NOT EXISTS idx_readings_device_metric_time
    ON telemetry_service.readings(device_id, metric_code, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_readings_recorded_at
    ON telemetry_service.readings(recorded_at DESC);

-- ALERT / TICKET SERVICE: alertas automáticas y reportes físicos de lectores.
CREATE TABLE IF NOT EXISTS alert_ticket_service.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    reading_id UUID NOT NULL,
    metric_code VARCHAR(50) NOT NULL,
    value NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    threshold_min NUMERIC(12, 4),
    threshold_max NUMERIC(12, 4),
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'abierta',
    reviewed_by_user_id INTEGER,
    reviewed_at TIMESTAMPTZ,
    resolved_by_user_id INTEGER,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_alert_severity CHECK (severity IN ('advertencia', 'critica')),
    CONSTRAINT chk_alert_status CHECK (status IN ('abierta', 'revisada', 'cerrada')),
    CONSTRAINT chk_alert_resolution CHECK (
        (status <> 'cerrada') OR (resolved_at IS NOT NULL AND resolved_by_user_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_alerts_device_status
    ON alert_ticket_service.alerts(device_id, status);
CREATE INDEX IF NOT EXISTS idx_alerts_status_created
    ON alert_ticket_service.alerts(status, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_alerts_active_device_metric
    ON alert_ticket_service.alerts(device_id, metric_code)
    WHERE status IN ('abierta', 'revisada');

CREATE TABLE IF NOT EXISTS alert_ticket_service.tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    created_by_user_id INTEGER NOT NULL,
    category VARCHAR(40) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'abierto',
    assigned_to_user_id INTEGER,
    resolved_by_user_id INTEGER,
    resolved_at TIMESTAMPTZ,
    closed_by_user_id INTEGER,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ticket_category CHECK (category IN ('carcasa_rota', 'tapa_faltante', 'etiqueta_ilegible', 'deterioro_estetico', 'otro')),
    CONSTRAINT chk_ticket_status CHECK (status IN ('abierto', 'en_revision', 'resuelto', 'cerrado')),
    CONSTRAINT chk_ticket_description CHECK (length(trim(description)) >= 10)
);

CREATE INDEX IF NOT EXISTS idx_tickets_device_status
    ON alert_ticket_service.tickets(device_id, status);
CREATE INDEX IF NOT EXISTS idx_tickets_creator_created
    ON alert_ticket_service.tickets(created_by_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_status_created
    ON alert_ticket_service.tickets(status, created_at DESC);

CREATE TABLE IF NOT EXISTS alert_ticket_service.ticket_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES alert_ticket_service.tickets(id) ON DELETE CASCADE,
    author_user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ticket_comment CHECK (length(trim(comment)) >= 1)
);

CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket_created
    ON alert_ticket_service.ticket_comments(ticket_id, created_at);

-- REPORT SERVICE: evidencia reproducible de reportes y acciones relevantes.
CREATE TABLE IF NOT EXISTS report_service.report_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(50) NOT NULL,
    generated_by_user_id INTEGER NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_report_type CHECK (report_type IN ('estado_laboratorio', 'alertas', 'tickets', 'telemetria'))
);

CREATE INDEX IF NOT EXISTS idx_report_snapshots_generated
    ON report_service.report_snapshots(generated_at DESC);

CREATE TABLE IF NOT EXISTS report_service.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id INTEGER,
    service_name VARCHAR(60) NOT NULL,
    action VARCHAR(80) NOT NULL,
    resource_type VARCHAR(60) NOT NULL,
    resource_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_actor_time
    ON report_service.audit_events(actor_user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource
    ON report_service.audit_events(resource_type, resource_id, occurred_at DESC);

DROP TRIGGER IF EXISTS trg_devices_updated_at ON device_service.devices;
CREATE TRIGGER trg_devices_updated_at BEFORE UPDATE ON device_service.devices
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_thresholds_updated_at ON device_service.thresholds;
CREATE TRIGGER trg_thresholds_updated_at BEFORE UPDATE ON device_service.thresholds
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_alerts_updated_at ON alert_ticket_service.alerts;
CREATE TRIGGER trg_alerts_updated_at BEFORE UPDATE ON alert_ticket_service.alerts
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_tickets_updated_at ON alert_ticket_service.tickets;
CREATE TRIGGER trg_tickets_updated_at BEFORE UPDATE ON alert_ticket_service.tickets
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
