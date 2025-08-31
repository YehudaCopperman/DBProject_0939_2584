
-- Procedure 2: update_expired_memberships.sql

CREATE OR REPLACE PROCEDURE public.update_expired_memberships()
AS $$
DECLARE
    v_today DATE := CURRENT_DATE;
    v_expire_date DATE;
BEGIN
    RAISE NOTICE 'Starting to update expired memberships...';

    -- לולאה המשתמשת בסמן מרומז
    FOR member_record IN (SELECT personid, memberstartdate, membershiptype FROM public.member WHERE isactive = TRUE) LOOP
        CASE member_record.membershiptype
            WHEN 'Monthly' THEN
                v_expire_date := member_record.memberstartdate + INTERVAL '1 month';
            WHEN 'Quarterly' THEN
                v_expire_date := member_record.memberstartdate + INTERVAL '3 months';
            WHEN 'Annual' THEN
                v_expire_date := member_record.memberstartdate + INTERVAL '1 year';
            ELSE
                CONTINUE; -- Ignore unsupported membership types
        END CASE;

        IF v_today >= v_expire_date THEN
            -- פקודת DML (UPDATE)
            UPDATE public.member
            SET isactive = FALSE
            WHERE personid = member_record.personid;
            RAISE NOTICE 'Membership for person ID % expired. Status updated to inactive.', member_record.personid;
        END IF;

    END LOOP;

    RAISE NOTICE 'Finished updating memberships.';

END;
$$ LANGUAGE plpgsql;