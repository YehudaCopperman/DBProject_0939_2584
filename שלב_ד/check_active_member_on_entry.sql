
-- Trigger 1: check_active_member_on_entry.sql

CREATE OR REPLACE FUNCTION public.check_active_member_on_entry()
RETURNS TRIGGER AS $$
DECLARE
    v_is_active BOOLEAN;
BEGIN
    SELECT isactive INTO v_is_active
    FROM public.member
    WHERE personid = NEW.personid;

    -- בדיקה והרמת חריגה
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Person with ID % is not a registered member.', NEW.personid;
    END IF;

    IF v_is_active IS FALSE THEN
        RAISE EXCEPTION 'Member with ID % is not active. Entry denied.', NEW.personid;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_member_status_trigger
BEFORE INSERT ON public.entryexit
FOR EACH ROW
EXECUTE FUNCTION public.check_active_member_on_entry();