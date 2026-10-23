-- Los usuarios se crean por auth-service; la migración debe ser segura si la
-- tabla aún no existe en una instalación nueva.
DO $$
BEGIN
    IF to_regclass('public.users') IS NOT NULL THEN
        ALTER TABLE public.users ALTER COLUMN google_id DROP NOT NULL;
    END IF;
END;
$$;
