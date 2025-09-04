-- 47-auth-role-simplify.sql
-- Roles policy:
--   admin  = EXISTS worker(pid=personid AND lower(job)='manager')
--   hourly = EXISTS hourly(pid=personid)
-- Everyone else -> no access.

CREATE OR REPLACE FUNCTION authenticate_user(p_username text, p_password text)
RETURNS TABLE (user_id int, personid int, role text)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT a.id,
         a.personid,
         CASE
           WHEN EXISTS (SELECT 1 FROM worker w WHERE w.pid = a.personid AND lower(w.job) = 'manager') THEN 'admin'
           WHEN EXISTS (SELECT 1 FROM hourly h WHERE h.pid = a.personid) THEN 'hourly'
           ELSE NULL
         END AS role
  FROM auth_user a
  WHERE a.username = p_username
    AND a.password_hash = crypt(p_password, a.password_hash)
    AND (
      EXISTS (SELECT 1 FROM worker w WHERE w.pid = a.personid AND lower(w.job) = 'manager')
      OR EXISTS (SELECT 1 FROM hourly h WHERE h.pid = a.personid)
    );
END;
$$;
