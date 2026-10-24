ALTER TABLE alert_ticket_service.tickets
    ADD COLUMN IF NOT EXISTS priority VARCHAR(20) NOT NULL DEFAULT 'no_critica';

ALTER TABLE alert_ticket_service.tickets
    DROP CONSTRAINT IF EXISTS chk_ticket_priority;

ALTER TABLE alert_ticket_service.tickets
    ADD CONSTRAINT chk_ticket_priority CHECK (priority IN ('no_critica', 'advertencia', 'critica'));
