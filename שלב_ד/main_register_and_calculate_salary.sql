
-- Main Program 1: main_register_and_calculate_salary.sql

DO $$
DECLARE
    v_salary NUMERIC;
    v_worker_pid INTEGER := 10101; -- דוגמה ל-PID של עובד שעתי
    v_month_year DATE := '2025-08-01';
BEGIN
    RAISE NOTICE 'Executing Main Program 1...';

    -- קריאה לפרוצדורה: רישום חבר חדש
    CALL public.register_new_member(
        10000,
        'Yael',
        'Cohen',
        '1995-05-20',
        'yael.c@example.com',
        'Tel Aviv',
        '5551234567',
        'Monthly'
    );

    -- קריאה לפונקציה: חישוב שכר
    v_salary := public.calculate_hourly_worker_salary(v_worker_pid, v_month_year);

    RAISE NOTICE 'Total salary for worker PID % in %: %', v_worker_pid, v_month_year, v_salary;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'An error occurred: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;