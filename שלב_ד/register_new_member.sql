
CREATE OR REPLACE PROCEDURE public.register_new_member(
    p_pid               integer,
    p_firstname         text,
    p_lastname          text,
    p_dateofb           date,
    p_email             text ,
    p_address           text ,
    p_phone             text ,         -- phone as text is safer than numeric
    p_membership_type   text,                      -- REQUIRED
    p_is_active         boolean DEFAULT TRUE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_type text;
BEGIN
    -- Normalize/validate membership type
    v_type := initcap(btrim(p_membership_type));   -- "monthly" -> "Monthly"
    IF v_type IS NULL OR v_type = '' THEN
        RAISE EXCEPTION 'membership_type is required (Monthly, Quarterly, Annual).';
    ELSIF v_type NOT IN ('Monthly','Quarterly','Annual') THEN
        RAISE EXCEPTION 'Unsupported membership_type "%". Allowed: Monthly, Quarterly, Annual.', v_type;
    END IF;

    -- Person must not already exist
    IF EXISTS (SELECT 1 FROM public.person WHERE pid = p_pid) THEN
        RAISE EXCEPTION 'A person with PID % already exists.', p_pid;
    END IF;

    INSERT INTO public.person(pid, dateofb, firstname, lastname, email, address, phone)
    VALUES (p_pid, p_dateofb, p_firstname, p_lastname, p_email, p_address, p_phone);

    INSERT INTO public.member(personid, memberstartdate, membershiptype, isactive)
    VALUES (p_pid, CURRENT_DATE, v_type, COALESCE(p_is_active, TRUE));

    RAISE NOTICE 'New member % % with membership type % registered successfully!',
                 p_firstname, p_lastname, v_type;
END;
$$;


