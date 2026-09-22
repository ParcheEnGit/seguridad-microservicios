-- Soporte opcional para acceso local de pruebas.
-- La columna es nula para preservar cuentas creadas con Google.
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
