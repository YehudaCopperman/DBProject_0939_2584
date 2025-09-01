DO $$
DECLARE
    v_cur REFCURSOR;
    rec   RECORD;
BEGIN
    RAISE NOTICE 'Executing Main Program 2...';

    -- 1) Update memberships
    CALL public.update_expired_memberships();

    -- 2) Get the opened refcursor from your function
    v_cur := public.get_active_repairs(
               TIMESTAMP '2025-01-01 00:00:00',
               TIMESTAMP '2025-08-31 23:59:59'
             );

    RAISE NOTICE 'Fetching active repairs...';

    LOOP
        FETCH NEXT FROM v_cur INTO rec;
        EXIT WHEN NOT FOUND;

        -- 6 placeholders, 6 args
        RAISE NOTICE 'Repair by % % (ID: %) on % for device ID % (%).',
            rec.firstname, rec.lastname, rec.personid,
            rec.date, rec.deviceid, rec.servicetype;
    END LOOP;

    CLOSE v_cur;
END;
$$ LANGUAGE plpgsql;
