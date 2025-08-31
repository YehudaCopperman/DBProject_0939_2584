-- Procedure 2: update_expired_memberships.sql
CREATE OR REPLACE PROCEDURE public.update_expired_memberships()
LANGUAGE plpgsql
AS $$
DECLARE
    v_today       DATE := CURRENT_DATE;
    v_expire_date DATE;
    member_record RECORD;  -- declare the loop record
BEGIN
    RAISE NOTICE 'Starting to update expired memberships...';

    FOR member_record IN
        SELECT personid, memberstartdate, membershiptype
        FROM public.member
        WHERE isactive = TRUE
    LOOP
        -- compute expire date; cast to DATE
        v_expire_date :=
            CASE member_record.membershiptype
                WHEN 'Monthly'   THEN (member_record.memberstartdate + INTERVAL '1 month')::date
                WHEN 'Quarterly' THEN (member_record.memberstartdate + INTERVAL '3 months')::date
                WHEN 'Annual'    THEN (member_record.memberstartdate + INTERVAL '1 year')::date
                ELSE NULL
            END;

        IF v_expire_date IS NULL THEN
            CONTINUE; -- unsupported type
        END IF;

        IF v_today >= v_expire_date THEN
            UPDATE public.member
            SET isactive = FALSE
            WHERE personid = member_record.personid
              AND isactive = TRUE;

            RAISE NOTICE 'Membership for person ID % expired. Status updated to inactive.', member_record.personid;
        END IF;
    END LOOP;

    RAISE NOTICE 'Finished updating memberships.';
END;
$$;
