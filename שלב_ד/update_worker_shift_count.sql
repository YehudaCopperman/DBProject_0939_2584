
-- Trigger 2: update_worker_shift_count.sql

CREATE OR REPLACE FUNCTION public.update_worker_shift_count()
RETURNS TRIGGER AS $$
BEGIN
    -- עדכון מונה המשמרות של העובד
    UPDATE public.worker
    SET total_shifts = (SELECT COUNT(*) FROM public.shift WHERE pid = NEW.pid)
    WHERE pid = NEW.pid;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER update_shifts_after_shift_change
AFTER INSERT OR UPDATE ON public.shift
FOR EACH ROW
EXECUTE FUNCTION public.update_worker_shift_count();