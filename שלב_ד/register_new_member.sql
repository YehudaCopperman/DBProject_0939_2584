
-- Procedure 1: register_new_member.sql

CREATE OR REPLACE PROCEDURE public.register_new_member(
    p_pid INTEGER,
    p_firstname VARCHAR,
    p_lastname VARCHAR,
    p_dateofb DATE,
    p_email VARCHAR DEFAULT NULL,
    p_address VARCHAR DEFAULT NULL,
    p_phone NUMERIC DEFAULT NULL,
    p_membership_type VARCHAR,
    p_is_active BOOLEAN DEFAULT TRUE
)
AS $$
BEGIN
    -- טיפול בחריגה עבור משתמש קיים
    IF EXISTS (SELECT 1 FROM public.person WHERE pid = p_pid) THEN
        RAISE EXCEPTION 'A person with PID % already exists.', p_pid;
    END IF;

    -- פקודות DML (INSERT)
    INSERT INTO public.person(pid, dateofb, firstname, lastname, email, address, phone)
    VALUES (p_pid, p_dateofb, p_firstname, p_lastname, p_email, p_address, p_phone);

    INSERT INTO public.member(personid, memberstartdate, membershiptype, isactive)
    VALUES (p_pid, CURRENT_DATE, p_membership_type, p_is_active);

    RAISE NOTICE 'New member % % with membership type % registered successfully!', p_firstname, p_lastname, p_membership_type;

END;
$$ LANGUAGE plpgsql;