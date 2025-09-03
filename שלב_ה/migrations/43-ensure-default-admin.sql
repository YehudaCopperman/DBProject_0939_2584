-- 43-ensure-default-admin.sql
-- Create a default admin (PID=1, user=1, pass=1) ONLY if there are NO admins at all.
-- Relies on v_user_roles (from 40-auth.sql) to detect current admins.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION ensure_default_admin()
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  -- אם אין בכלל אדמינים (על בסיס v_user_roles) – נייצר ברירת-מחדל
  IF NOT EXISTS (SELECT 1 FROM v_user_roles WHERE role = 'admin') THEN

    -- 1) ודא שיש person(1)
    IF NOT EXISTS (SELECT 1 FROM person WHERE pid = 1) THEN
      INSERT INTO person(pid, dateofb) VALUES (1, CURRENT_DATE);
    END IF;

    -- 2) ודא שיש worker(1) עם תפקיד "Manager"
    IF NOT EXISTS (SELECT 1 FROM worker WHERE pid = 1) THEN
      INSERT INTO worker(pid, job) VALUES (1, 'Manager');
    ELSE
      UPDATE worker SET job = 'Manager' WHERE pid = 1;
    END IF;

    -- 3) ודא חיבור ל-monthly (monthly."pId" הוא BIGINT)
    IF NOT EXISTS (SELECT 1 FROM monthly WHERE "pId" = 1) THEN
      INSERT INTO monthly("pId") VALUES (1);
    END IF;

    -- 4) ודא חשבון התחברות עם שם משתמש/סיסמה = '1'
    IF NOT EXISTS (SELECT 1 FROM auth_user WHERE personid = 1) THEN
      INSERT INTO auth_user(username, password_hash, personid)
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

-- אופציונלי: להריץ כבר עכשיו (לא חובה אם האפליקציה קוראת לזה בכל אתחול)
SELECT ensure_default_admin();
