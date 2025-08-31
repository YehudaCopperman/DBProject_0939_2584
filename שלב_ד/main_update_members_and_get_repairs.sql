
-- Main Program 2: main_update_members_and_get_repairs.sql

DO $$
DECLARE
    v_repairs_cursor REFCURSOR;
    v_repair_record RECORD;
BEGIN
    RAISE NOTICE 'Executing Main Program 2...';

    -- קריאה לפרוצדורה: עדכון סטטוס מנוי
    CALL public.update_expired_memberships();

    -- קריאה לפונקציה: קבלת רשימת שיפוצים באמצעות Ref Cursor
    SELECT public.get_active_repairs('2025-01-01 00:00:00', '2025-08-31 23:59:59') INTO v_repairs_cursor;

    RAISE NOTICE 'Fetching active repairs...';
    LOOP
        FETCH NEXT FROM v_repairs_cursor INTO v_repair_record;
        EXIT WHEN NOT FOUND;

        RAISE NOTICE 'Repair by % % (ID: %) on % for device ID % (%): %',
            v_repair_record.firstname, v_repair_record.lastname, v_repair_record.personid,
            v_repair_record.date, v_repair_record.deviceid, v_repair_record.servicetype;

    END LOOP;
    CLOSE v_repairs_cursor;

END;
$$ LANGUAGE plpgsql;