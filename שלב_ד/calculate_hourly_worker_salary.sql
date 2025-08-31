
-- Function 1: calculate_hourly_worker_salary.sql

CREATE OR REPLACE FUNCTION public.calculate_hourly_worker_salary(
    p_worker_pid INTEGER,
    p_month_year DATE
)
RETURNS NUMERIC AS $$
DECLARE
    v_total_salary NUMERIC := 0;
    v_regular_hours NUMERIC := 0;
    v_overtime_hours NUMERIC := 0;
    v_salary_ph NUMERIC;
    v_overtime_rate NUMERIC;
    v_shift_record RECORD;

    -- סמן מפורש (Explicit Cursor)
    shift_cursor CURSOR FOR
        SELECT date, clock_in, clock_out
        FROM public.shift
        WHERE pid = p_worker_pid AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM p_month_year) AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM p_month_year)
        ORDER BY date;
BEGIN
    -- טיפול בחריגה אם העובד אינו עובד שעתי
    SELECT salaryph, overtimerate INTO v_salary_ph, v_overtime_rate
    FROM public.hourly
    WHERE pid = p_worker_pid;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Worker with PID % is not an hourly worker.', p_worker_pid
        USING HINT = 'Please check the worker type in the hourly table.';
    END IF;

    -- לולאה באמצעות הסמן
    OPEN shift_cursor;
    LOOP
        FETCH shift_cursor INTO v_shift_record;
        EXIT WHEN NOT FOUND;

        DECLARE
            v_duration INTERVAL;
            v_hours NUMERIC;
            v_shift_end_time TIME;
        BEGIN
            v_shift_end_time := v_shift_record.clock_out;
            -- לוודא ששעות הסיום הגיוניות (במקרה של משמרת חצות)
            IF v_shift_end_time < v_shift_record.clock_in THEN
                v_duration := (v_shift_end_time + INTERVAL '24 hours') - v_shift_record.clock_in;
            ELSE
                v_duration := v_shift_end_time - v_shift_record.clock_in;
            END IF;

            v_hours := EXTRACT(EPOCH FROM v_duration) / 3600;

            -- הסתעפויות: חישוב שעות רגילות ושעות נוספות
            IF v_hours > 8 THEN
                v_regular_hours := v_regular_hours + 8;
                v_overtime_hours := v_overtime_hours + (v_hours - 8);
            ELSE
                v_regular_hours := v_regular_hours + v_hours;
            END IF;

        END;
    END LOOP;
    CLOSE shift_cursor;

    v_total_salary := (v_regular_hours * v_salary_ph) + (v_overtime_hours * v_overtime_rate * v_salary_ph);

    RETURN v_total_salary;

END;
$$ LANGUAGE plpgsql;