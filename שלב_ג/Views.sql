
-- view1 -- Financial Manager (financial_view)


CREATE VIEW financial_view AS
SELECT
    p.pid,
    p.firstname,
    p.lastname,
    s.servicename,
    sv.price,
    sv.servicedateb,
    sv.servicedatee,
    w.job,
    h.salaryph,
    h.overtimerate,
    CASE WHEN f.pid IS NOT NULL THEN TRUE ELSE FALSE END AS is_freelance,
    CASE WHEN h.pid IS NOT NULL THEN TRUE ELSE FALSE END AS is_hourly_worker
FROM
    public.person AS p
LEFT JOIN
    public.worker_1 AS w ON p.pid = w.pid
LEFT JOIN
    public.hourly_1 AS h ON w.pid = h.pid
LEFT JOIN
    public.freelance_1 AS f ON p.pid = f.pid
LEFT JOIN
    public.serves_1 AS sv ON f.pid = sv.pid
LEFT JOIN
    public.services_1 AS s ON sv.servicename = s.servicename;

-- query 1-- Total quarterly revenue from freelance workers.

SELECT
    pid AS id_number,
    firstname,
    lastname,
    EXTRACT(YEAR FROM servicedateb) AS service_year,
    EXTRACT(QUARTER FROM servicedateb) AS service_quarter,
    SUM(price) || ' ₪' AS total_quarterly_revenue
FROM
    financial_view
WHERE
    is_freelance = TRUE
GROUP BY
    pid, firstname, lastname, service_year, service_quarter
ORDER BY
    service_year, service_quarter, total_quarterly_revenue DESC;

-- query 2-- Total monthly pay for hourly workers including overtime.
SELECT
    fv.pid AS id_number,
    fv.firstname,
    fv.lastname,
    EXTRACT(MONTH FROM s.date) AS payroll_month,
    (SUM(CASE
        WHEN EXTRACT(EPOCH FROM (s.clock_out - s.clock_in)) / 3600 > 8 THEN
            8 * fv.salaryph + (EXTRACT(EPOCH FROM (s.clock_out - s.clock_in)) / 3600 - 8) * (fv.salaryph * fv.overtimerate)
        ELSE
            EXTRACT(EPOCH FROM (s.clock_out - s.clock_in)) / 3600 * fv.salaryph
    END)) || ' ₪' AS total_monthly_pay
FROM
    financial_view AS fv
JOIN
    public.shift_1 AS s ON fv.pid = s.pid
WHERE
    fv.is_hourly_worker = TRUE
GROUP BY
    fv.pid, fv.firstname, fv.lastname, payroll_month
ORDER BY
    payroll_month, total_monthly_pay DESC;






-- view2 -- Operations Manager (operations_view)
CREATE VIEW operations_view AS
SELECT
    ad.deviceid,
    ad.devicetype,
    ad.zoneid,
    ad.gymid,
    z.zonetype,
    g.name AS gym_name,
    ee.personid,
    ee.entrytime,
    ee.exittime,
    r.date AS repair_date,
    r.servicetype
FROM
    public.accessdevice AS ad
JOIN
    public.zone AS z ON ad.zoneid = z.zoneid AND ad.gymid = z.gymid
JOIN
    public.gym AS g ON z.gymid = g.gymid
LEFT JOIN
    public.entryexit AS ee ON ad.deviceid = ee.deviceid AND ad.zoneid = ee.zoneid AND ad.gymid = ee.gymid
LEFT JOIN
    public.repair AS r ON ad.deviceid = r.deviceid AND ad.zoneid = r.zoneid AND ad.gymid = r.gymid;


-- query 3-- Number of repairs per device type and gym, highlighting urgent repairs.
SELECT
    ov.gym_name,
    ov.devicetype,
    COUNT(ov.repair_date) AS number_of_repairs,
    COUNT(ov.repair_date) FILTER (WHERE ov.servicetype = 'Urgent Repair') AS urgent_repair_count
FROM
    operations_view AS ov
WHERE
    ov.repair_date IS NOT NULL
GROUP BY
    ov.gym_name, ov.devicetype
ORDER BY
    number_of_repairs DESC;

-- query 4-- Total entries per gym and zone type, categorized by membership type, including non-members.
SELECT
    ov.gym_name,
    ov.zonetype,
    -- COALESCE replaces NULL values with 'לא חבר'
    COALESCE(m.membershiptype, 'לא חבר') AS membershiptype,
    COUNT(ov.personid) AS total_entries
FROM
    operations_view AS ov
LEFT JOIN
    public.member AS m ON ov.personid = m.personid
-- Filter to include only rows where there was an actual entry
WHERE
    ov.entrytime IS NOT NULL
GROUP BY
    ov.gym_name,
    ov.zonetype,
    membershiptype
ORDER BY
    total_entries DESC;

