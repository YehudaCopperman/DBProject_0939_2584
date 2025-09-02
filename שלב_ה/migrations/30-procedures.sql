CREATE OR REPLACE PROCEDURE update_expired_memberships()
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE member
  SET isactive = FALSE
  WHERE memberenddate IS NOT NULL
    AND memberenddate < CURRENT_DATE
    AND isactive = TRUE;
END;
$$;

CREATE OR REPLACE PROCEDURE register_new_member(
  p_pid INT, p_firstname TEXT, p_lastname TEXT, p_dateofb DATE,
  p_email TEXT, p_address TEXT, p_phone BIGINT,
  p_membershiptype TEXT, p_isactive BOOLEAN
)
LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO person(pid, firstname, lastname, dateofb, email, address, phone)
  VALUES (p_pid, p_firstname, p_lastname, p_dateofb, p_email, p_address, p_phone)
  ON CONFLICT (pid) DO UPDATE
    SET firstname = EXCLUDED.firstname,
        lastname  = EXCLUDED.lastname,
        dateofb   = EXCLUDED.dateofb,
        email     = EXCLUDED.email,
        address   = EXCLUDED.address,
        phone     = EXCLUDED.phone;

  INSERT INTO member(personid, membershiptype, memberstartdate, isactive)
  VALUES (p_pid, p_membershiptype, CURRENT_DATE, p_isactive)
  ON CONFLICT (personid) DO UPDATE
    SET membershiptype = EXCLUDED.membershiptype,
        isactive       = EXCLUDED.isactive;
END;
$$;
