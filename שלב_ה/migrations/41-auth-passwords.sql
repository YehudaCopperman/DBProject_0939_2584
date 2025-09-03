-- 41-auth-passwords.sql
-- Default password = PID, change password (hourly), and admin reset.
-- Works with existing table: auth_user(id, username UNIQUE, password_hash, personid FK->person.pid)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Ensure an auth account exists for a given PID (username defaults to PID::text, password=PID)
CREATE OR REPLACE FUNCTION ensure_hourly_account(p_pid INT)
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM auth_user WHERE personid = p_pid) THEN
    INSERT INTO auth_user(username, password_hash, personid)
    VALUES (p_pid::text, crypt(p_pid::text, gen_salt('bf')), p_pid);
  END IF;
END;
$$;

-- Change password by PID (hourly self-service).
-- If the account doesn't exist yet, it is created with default password=PID,
-- and the user must provide the current (default) password to proceed.
CREATE OR REPLACE FUNCTION change_password_by_pid(p_pid INT, p_old TEXT, p_new TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql AS $$
DECLARE
  ok BOOLEAN := FALSE;
BEGIN
  PERFORM ensure_hourly_account(p_pid);

  SELECT (a.password_hash = crypt(p_old, a.password_hash))
  INTO ok
  FROM auth_user a
  WHERE a.personid = p_pid;

  IF NOT ok THEN
    RETURN FALSE; -- wrong current password
  END IF;

  UPDATE auth_user
  SET password_hash = crypt(p_new, gen_salt('bf'))
  WHERE personid = p_pid;

  RETURN TRUE;
END;
$$;

-- Admin reset password to default (PID).
-- App-level will ensure only admins can call this.
CREATE OR REPLACE FUNCTION admin_reset_password_by_pid(p_pid INT)
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  PERFORM ensure_hourly_account(p_pid);
  UPDATE auth_user
  SET password_hash = crypt(p_pid::text, gen_salt('bf'))
  WHERE personid = p_pid;
END;
$$;
