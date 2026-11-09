-- Soporte opcional para acceso local de pruebas.
-- La columna es nula para preservar cuentas creadas con Google.
-- En una instalación nueva auth-service crea la tabla ya con la columna.
DO $$
BEGIN
    IF to_regclass('public.users') IS NOT NULL THEN
        ALTER TABLE public.users
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
    END IF;
END;
$$;
