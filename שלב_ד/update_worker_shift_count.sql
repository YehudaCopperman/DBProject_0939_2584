
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




--not actually necessery but i did this anyway because otherwise it doesn't make sense to keep the shift hours if they are not all up to date.

-- recompute totals from existing shifts
UPDATE public.worker w
SET total_shifts = COALESCE(s.cnt, 0)
FROM (
  SELECT pid, COUNT(*) AS cnt
  FROM public.shift
  GROUP BY pid
) s
WHERE w.pid = s.pid;

-- any workers with no shifts become 0
UPDATE public.worker SET total_shifts = 0 WHERE total_shifts IS NULL;
