-- 45-admin-wizards.sql
-- Admin helpers that create all related records consistently.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Promote a PID to ADMIN:
-- Ensures person, worker(job='Manager', contract='Monthly', dateofeployment=today),
-- monthly("pId"=PID), and auth_user(username=PID, password=PID).
CREATE OR REPLACE FUNCTION admin_promote_to_admin(p_pid INT)
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  -- person
  IF NOT EXISTS (SELECT 1 FROM person WHERE pid = p_pid) THEN
    INSERT INTO person(pid, dateofb) VALUES (p_pid, CURRENT_DATE);
  END IF;

  -- worker (Manager / Monthly)
  IF NOT EXISTS (SELECT 1 FROM worker WHERE pid = p_pid) THEN
    INSERT INTO worker(job, contract, dateofeployment, pid, total_shifts)
    VALUES ('Manager', 'Monthly', CURRENT_DATE, p_pid, 0);
  ELSE
    UPDATE worker
      SET job = 'Manager',
          contract = 'Monthly',
          dateofeployment = COALESCE(dateofeployment, CURRENT_DATE)
      WHERE pid = p_pid;
  END IF;

  -- monthly
  IF NOT EXISTS (SELECT 1 FROM monthly WHERE "pId" = p_pid) THEN
    INSERT INTO monthly("pId") VALUES (p_pid);
  END IF;

  -- auth_user
  IF NOT EXISTS (SELECT 1 FROM auth_user WHERE personid = p_pid) THEN
    INSERT INTO auth_user(username, password_hash, personid)
    VALUES (p_pid::text, crypt(p_pid::text, gen_salt('bf')), p_pid);
  ELSE
    UPDATE auth_user
      SET username = p_pid::text,
          password_hash = crypt(p_pid::text, gen_salt('bf'))
      WHERE personid = p_pid;
  END IF;
END;
$$;

-- Promote a PID to HOURLY:
-- Ensures person, worker(contract='Hourly'), hourly row with sane defaults,
-- and auth_user(username=PID, password=PID).
CREATE OR REPLACE FUNCTION admin_promote_to_hourly(p_pid INT)
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  -- person
  IF NOT EXISTS (SELECT 1 FROM person WHERE pid = p_pid) THEN
    INSERT INTO person(pid, dateofb) VALUES (p_pid, CURRENT_DATE);
  END IF;

  -- worker (Hourly)
  IF NOT EXISTS (SELECT 1 FROM worker WHERE pid = p_pid) THEN
    INSERT INTO worker(job, contract, dateofeployment, pid, total_shifts)
    VALUES ('Clerk', 'Hourly', CURRENT_DATE, p_pid, 0);
  ELSE
    UPDATE worker
      SET contract = 'Hourly',
          dateofeployment = COALESCE(dateofeployment, CURRENT_DATE)
      WHERE pid = p_pid;
  END IF;

  -- hourly defaults (adjust if you need different defaults)
  IF NOT EXISTS (SELECT 1 FROM hourly WHERE pid = p_pid) THEN
    INSERT INTO hourly(pid, salaryph, overtimerate, bonus)
    VALUES (p_pid, 0, 1.25, 0);
  END IF;

  -- auth_user
  IF NOT EXISTS (SELECT 1 FROM auth_user WHERE personid = p_pid) THEN
    INSERT INTO auth_user(username, password_hash, personid)
    VALUES (p_pid::text, crypt(p_pid::text, gen_salt('bf')), p_pid);
  ELSE
    UPDATE auth_user
      SET username = p_pid::text,
          password_hash = crypt(p_pid::text, gen_salt('bf'))
      WHERE personid = p_pid;
  END IF;
END;
$$;
