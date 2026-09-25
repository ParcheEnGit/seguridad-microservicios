-- HU-10: trazabilidad explícita de las transiciones de estado de tickets.
-- La referencia a usuarios es lógica; public.users pertenece al auth-service.

CREATE TABLE IF NOT EXISTS alert_ticket_service.ticket_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES alert_ticket_service.tickets(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by_user_id INTEGER NOT NULL,
    note TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ticket_status_history_previous CHECK (
        previous_status IS NULL OR previous_status IN ('abierto', 'en_revision', 'resuelto', 'cerrado')
    ),
    CONSTRAINT chk_ticket_status_history_new CHECK (
        new_status IN ('abierto', 'en_revision', 'resuelto', 'cerrado')
    ),
    CONSTRAINT chk_ticket_status_history_transition CHECK (
        previous_status IS NULL OR previous_status <> new_status
    )
);

CREATE INDEX IF NOT EXISTS idx_ticket_status_history_ticket_time
    ON alert_ticket_service.ticket_status_history(ticket_id, changed_at);
