
--מודא שהמשכורות גדולות מ-0
-- 1  Ensure every hourly rate is positive
ALTER TABLE hourly
ADD CONSTRAINT chk_hourly_salary_positive
CHECK (salaryph > 0);

-- person 201 and matching worker row must already exist,
-- otherwise you’ll get a foreign‑key error first.

INSERT INTO hourly (salaryph, bonus, overtimerate, pid)
VALUES (0‑25.50,   500.00,   1.50,         201);

--מודא שזמן כניסה קודן לזמן יציאה
-- 2️ Validates that clock in is before clock out 
ALTER TABLE shift
ADD CONSTRAINT chk_shift_time_order
CHECK (clock_in < clock_out);


-- Assume pid 201 exists in HOURLY (or you’ll hit the FK first).

INSERT INTO shift (pid, "date", clock_in, clock_out)
VALUES (201, '2023-01-03', '18:00', '17:30');

-- מודא שמשמרת לא תהיה מדווחת על תאריך עתידי
-- 3️  makes sure that the shift is actually not after the current date

ALTER TABLE shift
ADD CONSTRAINT no_future_shifts
CHECK (date<=CURRENT_DATE)

--insert 9 digits
INSERT INTO shift (pid, "date", clock_in, clock_out)
VALUES (201, '2028-01-03', '16:00', '17:30');
