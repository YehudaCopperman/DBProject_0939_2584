-- 48-person-cascade-trigger.sql
-- Implements ON DELETE CASCADE semantics for person, using a trigger,
-- to support existing schema (even if FKs are missing or mismatched types).

CREATE OR REPLACE FUNCTION person_cascade_delete()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  -- Auth accounts
  DELETE FROM auth_user          WHERE personid = OLD.pid;

  -- Memberships
  DELETE FROM member             WHERE personid = OLD.pid;

  -- Workers (generic)
  DELETE FROM worker             WHERE pid = OLD.pid;
  -- Hourly / Monthly
  DELETE FROM hourly             WHERE pid = OLD.pid;
  DELETE FROM monthly            WHERE "pId" = OLD.pid;  -- monthly uses bigint pId

  -- Maintenance
  DELETE FROM maintenanceworker  WHERE personid = OLD.pid;

  -- Shifts & access logs
  DELETE FROM shift              WHERE pid = OLD.pid;
  DELETE FROM entryexit          WHERE personid = OLD.pid;

  RETURN OLD;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_trigger
    WHERE tgname = 'tr_person_cascade_delete'
  ) THEN
    CREATE TRIGGER tr_person_cascade_delete
    BEFORE DELETE ON person
    FOR EACH ROW
    EXECUTE FUNCTION person_cascade_delete();
  END IF;
END
$$;
