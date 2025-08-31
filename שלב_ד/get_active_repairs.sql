-- Function 2: get_active_repairs.sql  (named cursor)
CREATE OR REPLACE FUNCTION public.get_active_repairs(
    p_start_date timestamp,
    p_end_date   timestamp,
    OUT p_repairs_cursor refcursor
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- give the cursor a stable name
    p_repairs_cursor := 'repairs_cur';

    OPEN p_repairs_cursor FOR
        SELECT
            r.personid,
            p.firstname,
            p.lastname,
            r.date,
            r.deviceid,
            r.servicetype
        FROM public.repair r
        JOIN public.maintenanceworker mw ON r.personid = mw.personid
        JOIN public.person p            ON p.pid = mw.personid
        WHERE r.date >= p_start_date
          AND r.date <  p_end_date      -- half-open window is safer than BETWEEN
        ORDER BY r.date;
END;
$$;
