



--------------------------------------------
------------------select--------------------
--------------------------------------------



--Amount of hours each HOURLY worker worked for a given month   1
--שעות‑עבודה חודשיֹות לכל עובד   ‑   שעות בחודש נתון
SELECT firstname,lastname,sum(hours_worked) as total_hours
FROM person NATURAL JOIN  (
    SELECT  pid,date,
            (EXTRACT(EPOCH FROM (clock_out - clock_in))) / 3600 AS hours_worked
    FROM    shift
	)as time_worked
WHERE EXTRACT(MONTH FROM date)  =3 and EXTRACT(year FROM date) =2022
GROUP BY pid
ORDER   BY total_hours DESC;



--The amount each shifts cost (need to take overtime into account)  2
 /* 2) מחשבים את משך המשמרת בשעות */
WITH shift_durations AS (
    SELECT  s.pid,
            s.date,
            EXTRACT(EPOCH FROM (s.clock_out - s.clock_in)) / 3600 AS hours_worked
    FROM    shift AS s
),
pay_calc AS (
    SELECT  d.pid,
            d.date,
            d.hours_worked,
            h.salaryph,
            h.bonus,
            d.hours_worked * h.salaryph                                AS base_salary,
            GREATEST(d.hours_worked - 8, 0) * h.salaryph * (h.overtimerate-1) AS extra_payment
    FROM    shift_durations d
    JOIN    hourly h USING (pid)
)
SELECT  p.pid,
        p.firstname,
        p.lastname,
        c.date,
		c.salaryph,
		ROUND(c.hours_worked,2)AS hours_worked,
        ROUND(c.base_salary, 2)      AS base_salary,
        ROUND(c.extra_payment, 2)    AS extra_payment_for_bonus
FROM    pay_calc   c
JOIN    person     p USING (pid)
ORDER   BY p.pid, c.date;

--The amount the whole month cost(need to take bonus into account)
--3כמה  עובד  מסוים הכניס כל חודש
SELECT pid,firstname, lastname,extract(YEAR FROM date )AS year,extract(MONTH FROM date )AS MONTH,SUM((EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600)*salaryph) as base_salary_month,SUM(GREATEST((EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600)-8,0)*salaryph*(overtimerate-1)) as extra_payment_for_bonus 
FROM person NATURAL JOIN shift NATURAL JOIN hourly 
where pid=300
GROUP BY pid,extract(YEAR FROM date ),extract(MONTH FROM date )
order by extract(year FROM date ),extract(MONTH FROM date )

--4
--השירות עבורו הוציאו הכי הרבה כסף
---Name of service that was spent on the most so far        
with listoftotals as(select servicename , sum(price)as total
from serves

group by servicename)
select servicename as most_expensive_service,total 
from listoftotals
where total = (select max(total) from listoftotals)

-- הספק הכי זול עבור כל שירות
--5--Cheapest provider for each service given till now       
select pid, firstname , lastname,servicename,price as cheapest_price
from serves as b natural join person
where price =(select min(price)
				from serves
				where servicename=b.servicename)



/* --6-- סיכום שעות עבודה לכל תפקיד  –  חודש לדוגמה (מרץ 2025)  */
WITH shift_hours AS (
    SELECT  w.job,
            s.pid,
            EXTRACT(EPOCH FROM (s.clock_out - s.clock_in))/3600 AS hrs
    FROM    shift   s
    JOIN    worker  w USING (pid)
    WHERE   extract(MONTH FROM date)  = 5 and extract(Year FROM date ) = 2022
)
SELECT  job                                           ,
        COUNT(DISTINCT pid)                        AS amount_of_workers,
        ROUND(SUM(hrs), 2)                         AS total_work_time,
        ROUND(SUM(hrs) / COUNT(DISTINCT pid), 2)   AS ave_hours_per_person
FROM    shift_hours
GROUP   BY job
ORDER   BY ROUND(SUM(hrs) / COUNT(DISTINCT pid), 2)  DESC;









-- שאילתא 7
--תיאור**: מראה את כמות העובדים מכל משרה מעל 65 (ככה תדע מי יוצא לפנסיה ולפי זה תעסיק עובדים חדשים)  

with elderly_workers_per_job as (
		select job,sum(1) as amount_of_employees
		from person  join  worker on person.pid = worker.pid
		left outer join hourly on worker.pid = hourly.pid
		left outer join monthly on worker.pid = monthly.pid
		where dateofb < CURRENT_DATE - INTERVAL '65 year'
		group by job
),
select * 
from elderly_workers_per_job


--8
-- השאילתא מראה את 10 העובדים עם חוזה שעתי שיש להם הכי הרבה אוברטיים יחסית לשעות עבודה רגילות
with overtime_percentage as(
			select pid,date,ROUND(LEAST(EXTRACT(EPOCH FROM (s.clock_out - s.clock_in)) / 3600,8),2)as basic,
			ROUND(GREATEST(EXTRACT(EPOCH FROM (s.clock_out - s.clock_in)) / 3600-8,0),2)as overtime
			from hourly h natural join shift s
			ORDER BY pid
), our_months_we_care_about as(
select *,Round(overtime/(basic+overtime),2)as overtime_proportion
from overtime_percentage
where extract(year from date)=2023 and extract(month from date)>=2)


select pid, sum(basic) as month_basic, 
			sum(overtime) as month_overtime,
			ROUND(sum(overtime)*100/sum(basic +overtime),6) as proportion_over_the_month
from our_months_we_care_about
group by pid
order by proportion_over_the_month desc LIMIT 100






--------------------------------------------
----------------updates---------------------
--------------------------------------------





--Update salaries of workers who did more than 160 hours in 2022 5 to 1.05 time more 

UPDATE hourly AS h
SET    salaryph = ROUND(salaryph * 1.05, 2)          -- keep two decimals
FROM  (
        SELECT  pid,max(salaryph),max(date)as wert
        FROM    shift natural join hourly
        WHERE   extract(MONTH FROM date)=5 and extract(YEAR FROM date)= 2022
        GROUP BY pid
        HAVING  SUM(EXTRACT(EPOCH FROM (clock_out - clock_in)))/3600 > 16
      ) AS big_month
WHERE  h.pid = big_month.pid
RETURNING h.pid, salaryph;            -- see who got bumped


--נותן עוד יום חופש למי שיש יותר מוותק מסוים
--Gives an extra vacation day for whomever was employed before 2022 3
UPDATE monthly AS m
SET    vacationdays = vacationdays + 1
FROM   worker  w
WHERE  m.pid = w.pid
  AND  w.dateOfEployment <= CURRENT_DATE - INTERVAL '2 years'
RETURNING m.pid, m.vacationdays;

--עדכון  שכר עבור שכיר בחוזה שעתי מסוים
--Update hourly someone's salary (this is an example of pid 102 given some random raise)
UPDATE hourly
SET    salaryph = salaryph + 2.50,      -- new hourly rate
       bonus     = bonus + 250.00       -- one‑time bonus
WHERE  pid = 102
RETURNING pid, salaryph, bonus;


--עדכון  שכר עבור שכיר בחוזה חדשי מסוים
--Update monthly worker salary
UPDATE monthly
SET    salarypm         = salarypm + 1000,
       vecationdays     = vecationdays + 2,
       benefits_package = benefits_package || '; Dental'
WHERE  pid = 456
RETURNING pid, salarypm, vecationdays, benefits_package;


--------------------------------------------
------------------delete---------------------
--------------------------------------------


--1 -מוחק את כל הפרילנסרים שאין להם שום שירות רשום בserves 
DELETE FROM freelance f
WHERE NOT EXISTS (
    SELECT 1
    FROM serves s
    WHERE s.pid = f.pid
      
);

--2 deletes workers that aren't in either hourly or monthly tables
DELETE FROM worker AS w
WHERE NOT EXISTS (SELECT 1 FROM hourly    h WHERE h.pid = w.pid)
  AND NOT EXISTS (SELECT 1 FROM monthly   m WHERE m.pid = w.pid);


--3 deletes shifts that are shorter than an hour
DELETE FROM shift
WHERE EXTRACT(EPOCH FROM (clock_out - clock_in)) / 60 < 60;
--just so it would be clear the difference of the results
select *, EXTRACT(EPOCH FROM (clock_out - clock_in))/60 as minutes 
from shift order by EXTRACT(EPOCH FROM (clock_out - clock_in));

--------------------נספח-------------------------------
-----------------queries that weren't used in the end but might be helpful in the future------------


--List of each service how much money was spent on it

  
SELECT servicename ,sum(price)as total_cost
FROM serves 
GROUP BY servicename



-- 4כמה כל עובד הכניס בחודש נתון וכמה שעות עבד
  WITH shift_durations AS (
    SELECT  s.pid,
            s.date,
            EXTRACT(EPOCH FROM (s.clock_out - s.clock_in)) / 3600 AS hours_worked
    FROM    shift AS s
)
SELECT pid,firstname, lastname,ROUND(SUM(hours_worked),2) as hours,ROUND(SUM(hours_worked*salaryph) + SUM(GREATEST(hours_worked-8,0)*salaryph*(overtimerate-1)) +max(bonus),2) as total_pay 
FROM person NATURAL JOIN shift_durations NATURAL JOIN hourly 
where extract(YEAR FROM date )= 2022 and extract (MONTH FROM date )=8
GROUP BY pid,extract(YEAR FROM date ),extract(MONTH FROM date )
order by extract(year FROM date ),extract(MONTH FROM date ) 



--5 כמה כל עובד הכניס כל חודש 

with  payment_per_shift as(SELECT pid,overtimerate,EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600 as hours_,date,(EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600)*salaryph as base_salary,GREATEST((EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600)-8,0)*salaryph*(overtimerate-1) as extra_payment_for_overtime
FROM shift NATURAL JOIN hourly ) 

  
SELECT pid,firstname, lastname,extract(Year FROM date )as year_,extract(MONTH FROM date) as month_,SUM(base_salary) as base_salary_month,SUM(extra_payment_for_overtime) as overtime_over_the_month 
FROM person NATURAL JOIN payment_per_shift
GROUP BY pid,extract(Year FROM date ),extract(MONTH FROM date)
order by pid