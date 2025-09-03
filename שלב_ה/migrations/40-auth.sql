-- =============================================================================
-- 40-auth.sql
-- Authentication/Authorization bootstrap for the Gym DB GUI
-- =============================================================================
-- Overview
--   - Minimal credentials table (auth_user) mapping a login to person(pid).
--   - Role is derived from your HR hierarchy:
--       * monthly + worker.job ~ 'manager'  → role='admin'   (forgiving spelling)
--       * hourly                              → role='hourly'
--       * otherwise                           → role='denied'
--   - Safe login function: authenticate_user(username, password)
--     returns (user_id, personid, role).
--
-- Security: uses pgcrypto (crypt + gen_salt('bf')) for salted password hashes.
-- Idempotent: CREATE IF NOT EXISTS / CREATE OR REPLACE.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) Credentials table (login only)
CREATE TABLE IF NOT EXISTS auth_user (
  id            SERIAL PRIMARY KEY,
  username      TEXT UNIQUE NOT NULL,
  password_hash TEXT        NOT NULL,
  personid      INT         NOT NULL REFERENCES person(pid) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auth_user_personid ON auth_user(personid);

-- 2) Role derivation view
-- NOTE:
--   - monthly."pId" is bigint → cast to INT to match worker/person pid
--   - worker.job is used as the “title”.
--   - Normalize as: regexp_replace(lower(w.job), '[^a-z]', '', 'g')
--     so "Manager", "MANAGER", "maneger" → 'manager'/'maneger'
CREATE OR REPLACE VIEW v_user_roles AS
SELECT
  au.id        AS user_id,
  au.username,
  au.personid,
  CASE
    WHEN EXISTS (
      SELECT 1
      FROM monthly m
      JOIN worker  w ON w.pid = m."pId"::INT
      WHERE w.pid = au.personid
        AND regexp_replace(lower(w.job), '[^a-z]', '', 'g') IN ('manager','maneger')
    ) THEN 'admin'
    WHEN EXISTS (
      SELECT 1
      FROM hourly h
      WHERE h.pid = au.personid
    ) THEN 'hourly'
    ELSE 'denied'
  END AS role
FROM auth_user au;

-- 3) Authentication function
-- Usage:  SELECT * FROM authenticate_user('user','pass');
-- Returns: (user_id INT, personid INT, role TEXT)
CREATE OR REPLACE FUNCTION authenticate_user(p_username TEXT, p_password TEXT)
RETURNS TABLE(user_id INT, personid INT, role TEXT)
LANGUAGE plpgsql
AS $auth$
BEGIN
  RETURN QUERY
  SELECT v.user_id, v.personid, v.role
  FROM v_user_roles v
  JOIN auth_user a ON a.id = v.user_id
  WHERE a.username = p_username
    AND a.password_hash = crypt(p_password, a.password_hash);
END;
$auth$;

-- 4) Seed users (idempotent)
-- Admin seed: first monthly employee whose job ~ 'manager'/'maneger'
INSERT INTO auth_user (username, password_hash, personid)
SELECT 'admin', crypt('admin123', gen_salt('bf')), w.pid
FROM monthly m
JOIN worker  w ON w.pid = m."pId"::INT
WHERE regexp_replace(lower(w.job), '[^a-z]', '', 'g') IN ('manager','maneger')
LIMIT 1
ON CONFLICT (username) DO NOTHING;

-- Hourly seed: first hourly employee
INSERT INTO auth_user (username, password_hash, personid)
SELECT 'worker1', crypt('worker123', gen_salt('bf')), h.pid
FROM hourly h
LIMIT 1
ON CONFLICT (username) DO NOTHING;
