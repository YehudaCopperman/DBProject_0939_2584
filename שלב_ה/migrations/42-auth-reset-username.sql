-- 42-auth-reset-username.sql
-- Admin reset: username := PID::text, password := PID::text

CREATE OR REPLACE FUNCTION admin_reset_password_by_pid(p_pid INT)
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  -- נוודא שקיים חשבון (אם לא, ניצור עם ברירת מחדל)
  PERFORM ensure_hourly_account(p_pid);

  -- נאפס גם סיסמה וגם שם משתמש ל-PID
  UPDATE auth_user
  SET password_hash = crypt(p_pid::text, gen_salt('bf')),
      username      = p_pid::text
  WHERE personid = p_pid;
END;
$$;
