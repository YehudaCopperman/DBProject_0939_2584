
-- Function 2: get_active_repairs.sql

CREATE OR REPLACE FUNCTION public.get_active_repairs(
    p_start_date TIMESTAMP,
    p_end_date TIMESTAMP,
    OUT p_repairs_cursor REFCURSOR
)
AS $$
BEGIN
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
        JOIN public.person p ON mw.personid = p.pid
        WHERE r.date BETWEEN p_start_date AND p_end_date
        ORDER BY r.date;

END;
$$ LANGUAGE plpgsql;