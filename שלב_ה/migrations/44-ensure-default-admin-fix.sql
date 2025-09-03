-- 44-ensure-default-admin-fix.sql
-- Fix ensure_default_admin(): fill required NOT NULL columns in worker (contract, dateofeployment).

CREATE OR REPLACE FUNCTION ensure_default_admin()
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  -- Only if there are NO admins at all (based on v_user_roles)
  IF NOT EXISTS (SELECT 1 FROM v_user_roles WHERE role = 'admin') THEN

    -- 1) person(1)
    IF NOT EXISTS (SELECT 1 FROM person WHERE pid = 1) THEN
      INSERT INTO person (pid, dateofb) VALUES (1, CURRENT_DATE);
    END IF;

    -- 2) worker(1) with required fields:
    --    job='Manager', contract='Monthly', dateofeployment=CURRENT_DATE
    IF NOT EXISTS (SELECT 1 FROM worker WHERE pid = 1) THEN
      INSERT INTO worker (job, contract, dateofeployment, pid)
      VALUES ('Manager', 'Monthly', CURRENT_DATE, 1);
    ELSE
      UPDATE worker
      SET job = 'Manager',
          contract = COALESCE(contract, 'Monthly'),
          dateofeployment = COALESCE(dateofeployment, CURRENT_DATE)
      WHERE pid = 1;
    END IF;

    -- 3) monthly("pId"=1)
    IF NOT EXISTS (SELECT 1 FROM monthly WHERE "pId" = 1) THEN
      INSERT INTO monthly ("pId") VALUES (1);
    END IF;

    -- 4) auth_user for pid=1 (username/password = '1')
    IF NOT EXISTS (SELECT 1 FROM auth_user WHERE personid = 1) THEN
      INSERT INTO auth_user (username, password_hash, personid)
      VALUES ('1', crypt('1', gen_salt('bf')), 1);
    ELSE
      UPDATE auth_user
      SET username = '1',
          password_hash = crypt('1', gen_salt('bf'))
      WHERE personid = 1;
    END IF;

  END IF;
END;
$$;
