UPDATE alert_ticket_service.tickets
SET priority = CASE
    WHEN description ~* 'Severidad:\s*Crítica' THEN 'critica'
    WHEN description ~* 'Severidad:\s*Advertencia' THEN 'advertencia'
    ELSE priority
END
WHERE priority = 'no_critica'
  AND description ~* 'Severidad:\s*(Crítica|Advertencia)';
