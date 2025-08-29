# רשת חדרי כושר  
מערכת תשלומי עובדים  

**מגישים:**  
משה גודמן 770120939  
יהודה קופרמן 207012584




## תוכן עניינים



 [שלב א](#שלב-א)   
> [אודות הפרויקט](#אודות-הפרויקט)     
[ישויות](#ישויות)       
[ דיאגרמת ישות יחסים ](#דיאגרמת-ישות-יחסים )      
[ סכמה רלציונית](#סכמה-רלציונית )  
[קבצי יצירה ואכלוס בסיס הנתונים](#קבצי-יצירה-ואכלוס-בסיס-הנתונים)    
[הכנסת ערכים לבסיס נתונים](#הכנסה-לבסיס-נתונים)  
[גיבוי ושחזור](#גיבוי-ושחזור)  

 [שלב ב](#שלב-ב) 
> [שאילתות SELECT](#שאילתות-SELECT)    
[שאילתות עדכון (UPDATE)](#שאילתות-UPDATE)    
[שאילתות מחיקה (DELETE)](#שאילתות-DELETE)    
[אילוצים (Constraints)](#אילוצים)  
[ commit and rollback](#commit-and-rollback)  

[שלב ג](#שלב-ג)  
> [אינטגרציה ומבטים](#אינטגרציה-ומבטים)  
> [קוד חילוץ מבנה הנתונים (DSD)](#dsdקוד-חילוץ-מבנה-הנתונים)  
> [פלט מהקוד – תרשים מבנה בסיס הנתונים](#פלט-הקוד-תרשים-מבנה-בסיס-הנתונים)  
> [תרשים ישויות ויחסים (ERD)](#תרשים-ישויות-ויחסיםerd)
> [מבטים ןשאילתות](#מבטים ושאילתות)


## שלב א
### אודות-הפרויקט
במסגרת הפרויקט הכיתתי שמטרתו להפעיל רשת מכוני כושר.  
 תת‑הפרויקט הנוכחי מוקדש לניהול העובדים במערכת. הוא יכלול ריכוז כל הנתונים הנוגעים אליהם—החל מפרטים אישיים, משכורת, ותק ובונוסים ועד לחוזה ההעסקה ולתפקידם—ולצד זאת יבטיח גישה נוחה ובטוחה למידע.


### ישויות  
* **אנשים** (**מס מזהה**, תאריך לידה, שם פרטי , שם משפחה , כתובת מייל , כתובת, מס טלפון)  
    * **שכיר** (**מס מזהה**,תפקיד , חוזה , תאריך העסקה)  
        * **עובד לפי שעה** (**מס מזהה** , שכר שעתי , בונוס חודשי , אוברטיים)  
            * **משמרת**(**מס מזהה**, תאריך , שעת כניסה , שעת יציאה)
        * **עובד חדשי** (**מס מזהה** , שכר חודשי , מס ימי חופשה , חבילת הטבות)
    * **נותן שירות חיצוני**(**מס מזהה**)
* **שירותים**(**שם השירות**, ציוד נדרש)
* **מתן שירות** (**מס מזהה** , **שם השירות** , מחיר , חוזה , תאריך תחילת שירות, תאריך סיום)

 
we might wanna add also tax and pension plans to the tables  
maybe it is better to combine the shift and timespan into one table (put into consideration whether you want to have workers clock in twice for the same time)  
we created the ERD and relational schema as shown in the pictures below  


### דיאגרמת ישות יחסים 

קישור לקובץ erdplus : 
[דיאגרמת ישויות](DBProject_0939_2584/שלב%20א/gym_people_erd_diagram.erdplus)

<img src="for_md/people_erd_diagram.png" width="600" height="400" />  


### סכמה רלציונית
קישור לקובץ erdplus :
 [סכמה רלציונית](DBProject_0939_2584/שלב%20א/gym_people_relational_schema.erdplus)


<img src="for_md/relational_schema.png"  />    


## קבצי יצירה ואכלוס בסיס הנתוני  
[יצירה CREATE](DBProject_0939_2584/שלב%20א/createTable.sql)  
[מחיקה DROP](DBProject_0939_2584/שלב%20א/dropTable.sql)  
[הכנסת ערכים  INSERT](DBProject_0939_2584/שלב%20א/insertTables.sql)    
[קריאת הנתונים SELECT](DBProject_0939_2584/שלב%20א/selectAll.sql)   

### הכנסה לבסיס נתונים  
[אנשים](DBProject_0939_2584/שלב%20א/pdadmin_import/freelance.csv)    
[שכיר](DBProject_0939_2584/שלב%20א/pdadmin_import/worker.csv)    
[שכיר חודשי](DBProject_0939_2584/שלב%20א/pdadmin_import/hourly.csv)    
[שכיר לפי שעה](DBProject_0939_2584/שלב%20א/pdadmin_import/freelance.csv)    
[סןג שירות חיצוני](DBProject_0939_2584/שלב%20א/pdadmin_import/services.csv)    
[מתן שירות חיצוני](DBProject_0939_2584/שלב%20א/pdadmin_import/serves.csv)    
### קבצי הרשומות  

## here are three ways where we added data to the tables
1. python copying from shift.csv file using postgres command  
<img src="for_md/python_postgres.png"  />      
3. python using pandas library
<img src="for_md/pandas.png"  />      
5. using the pgadmin interface (pressing the import button.png)    
<img src="for_md/pgadmin_import_button.png"  />      
6. using the query tool in pgadmin  
<img src="for_md/pgadmin_query_tool.png"  />      


below is the picture of the backup and restoration    
## גיבוי ושחזור  
[קובץ הגיבוי](DBProject_0939_2584/שלב%20א/backup_03_04_2025.sql)   

<img src="for_md/backup_screenshot.png"  />      
<img src="for_md/restoration.jpg"  />      




# שלב ב
## שאילתות SELECT
### שאילתא 1
**תיאור**: השאילתא מראה את שעות העבודה של כל עובד והתשלום שמקבל בחודש נתון  
**הקוד** : 
```
SELECT firstname,lastname,sum(hours_worked) as total_hours
FROM person NATURAL JOIN  (
    SELECT  pid,date,
            (EXTRACT(EPOCH FROM (clock_out - clock_in))) / 3600 AS hours_worked
    FROM    shift
	)as time_worked
WHERE EXTRACT(MONTH FROM date)  =3 and EXTRACT(year FROM date) =2022
GROUP BY pid
ORDER   BY total_hours DESC;
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image.png)


### שאילתא 2

**תיאור**: השאילתא מראה השכר עבור משמרת אחת  
**הקוד** : 
```
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
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image-1.png)

### שאילתא 3
**תיאור**: השאילתא מראה עבור עובד מסוים את כל המשכורות החודשיות שלו  
**הקוד** : 
```
SELECT pid,firstname, lastname,extract(YEAR FROM date )AS year,extract(MONTH FROM date )AS MONTH,SUM((EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600)*salaryph) as base_salary_month,SUM(GREATEST((EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600)-8,0)*salaryph*(overtimerate-1)) as extra_payment_for_bonus ,max(bonus)as bonus
FROM person NATURAL JOIN shift NATURAL JOIN hourly 
where pid=300
GROUP BY pid,extract(YEAR FROM date ),extract(MONTH FROM date )
order by extract(year FROM date ),extract(MONTH FROM date )
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image-2.png)


### שאילתא 4
**תיאור**: השירותים עבורם הוציאו הכי הרבה כסף
**הקוד** : 
```
with listoftotals as(select servicename , sum(price)as total
from serves

group by servicename)
select servicename as most_expensive_service,total 
from listoftotals
where total = (select max(total) from listoftotals)
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image-3.png)

### שאילתא 5
**תיאור**: הספק הכי זול עבור כל שירות  
**הקוד** : 
```
select pid, firstname , lastname,servicename,price as cheapest_price
from serves as b natural join person
where price =(select min(price)
				from serves
				where servicename=b.servicename)
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image-4.png)

### שאילתא 6 
יכום שעות עבודה לכל תפקיד  –  חודש לדוגמה (מרץ 2022) 
**תיאור**:   
**הקוד** : 
```
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
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image-5.png)

### שאילתא 7
**תיאור**: מראה את כמות העובדים מכל משרה מעל 65 (ככה תדע מי יוצא לפנסיה ולפי זה תעסיק עובדים חדשים)  
**הקוד** : 
```
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
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image-32.png)  


### שאילתא 8
**תיאור**: השאילתא מראה את 10 העובדים עם חוזה שעתי שיש להם הכי הרבה אוברטיים יחסית לשעות עבודה רגילות  
**הקוד** : 
```
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
```
**התוצאה** :  
![alt text](for_md/for_second_stage/image-33.png)
 


## שאילתות UPDATE

### שאילתת update 1 
**תיאור**: נותן עוד יום חופש למי שיש יותר מוותק מסוים  
**הקוד**: 
```
UPDATE monthly AS m
SET    vacationdays = vacationdays + 1
FROM   worker  w
WHERE  m.pid = w.pid
  AND  w.dateOfEployment <= CURRENT_DATE - INTERVAL '2 years'
RETURNING m.pid, m.vacationdays;
```

**לפני**    
![alt text](for_md/for_second_stage/image-6.png)  
**אחרי**  
![alt text](for_md/for_second_stage/image-12.png)


### שאילתת update 2 
**תיאור**:   עדכון נתוני שכר  
**הקוד**: 
```
UPDATE hourly
SET    salaryph = salaryph + 2.50,      
       bonus     = bonus + 250.00       
WHERE  pid = 102
RETURNING pid, salaryph, bonus;
```  
**לפני**    
![alt text](for_md/for_second_stage/image-13.png)  
**אחרי**    
![alt text](for_md/for_second_stage/image-14.png)




### שאילתת update 3 
**תיאור**:  מקפיץ את המשכורת של כל מי שעבד בחודש נתון ב5%  (5/2022)  
**הקוד**: 
```

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
RETURNING h.pid, salaryph;       
```
**(השאילתא לראות את מה שצריך לפני)**
```
select pid,salaryph
from hourly natural join shift
WHERE   extract(MONTH FROM date)=5 and extract(YEAR FROM date)= 2022
GROUP BY pid
HAVING  SUM(EXTRACT(EPOCH FROM (clock_out - clock_in)))/3600 > 16
order by pid
```


**לפני**    
![alt text](for_md/for_second_stage/image-10.png)   
 **אחרי**  
![alt text](for_md/for_second_stage/image-11.png)








##  שאילתות DELETE  


### שאילתת delete 1   
**תיאור**:  -מוחק את כל הפרילנסרים שאין להם שום שירות רשום ב-serves        
**הקוד**:   
```
DELETE FROM freelance f
WHERE NOT EXISTS (
    SELECT 1
    FROM serves s
    WHERE s.pid = f.pid
      
);
```

**לפני**  
![alt text](for_md/for_second_stage/image-34.png)    
**אחרי**    
![alt text](for_md/for_second_stage/image-35.png)  




### שאילתת delete 2  
**תיאור**: מוחק עובדים שלא נמצאים בחוזהה חודשי ולא בחוזה שנתי     
**הקוד**:   
```
DELETE FROM worker AS w
WHERE NOT EXISTS (SELECT 1 FROM hourly    h WHERE h.pid = w.pid)
  AND NOT EXISTS (SELECT 1 FROM monthly   m WHERE m.pid = w.pid);
```

**לפני**   
![alt text](for_md/for_second_stage/image-36.png) 
**אחרי**    
![alt text](for_md/for_second_stage/image-37.png)   



### שאילתת delete 3   
**תיאור**:  מעיף כל משמרת שהיתה פחות משעה    
**הקוד**:   
```
DELETE FROM shift
WHERE EXTRACT(EPOCH FROM (clock_out - clock_in)) / 60 < 60;



```
**יעזור לראות**  
```
select *, EXTRACT(EPOCH FROM (clock_out - clock_in))/60 as minutes 
from shift order by EXTRACT(EPOCH FROM (clock_out - clock_in));

```
**לפני**   
![alt text](for_md/for_second_stage/image-38.png)   

**אחרי**    
![alt text](for_md/for_second_stage/image-39.png)  
  




## אילוצים

### אילוץ 1  
**תיאור:** מחייב שהמשכורות גדולות מ-0
  
**הקוד**  
```
ALTER TABLE hourly
ADD CONSTRAINT chk_hourly_salary_positive
CHECK (salaryph > 0);
```
**כישלון בעקבות האילוץ**  
![alt text](for_md/for_second_stage/image-15.png)



### אילוץ 2  
**תיאור:** מחייב שהכניסה תהיה לפני היציאה
  
**הקוד**  
```
ALTER TABLE shift
ADD CONSTRAINT chk_shift_time_order
CHECK (clock_in < clock_out);

```
**כישלון בעקבות האילוץ**  
![alt text](for_md/for_second_stage/image-16.png)

### אילוץ 3
**תיאור:** מחייב שמשמרת לא תהיה מדווחת על תאריך עתידי  

**הקוד**  
```
ALTER TABLE shift
ADD CONSTRAINT chk_shift_time_order
CHECK (clock_in < clock_out);

```
**כישלון בעקבות האילוץ**  
![alt text](for_md/for_second_stage/image-17.png)



##  commit and rollback

### ראשון
**תיאור**: מוחק את כל נתוני השירות לפני תאריך נתון (נתונים ישנים לא מעניינים)

**לפני מחיקת כל השירותים לפני 2022-07-10**  
![alt text](for_md/for_second_stage/image-18.png)  

**אחרי מחיקת כל השירותים לפני 2022-07-10**  
![alt text](for_md/for_second_stage/image-19.png)  

**אחרי רולבק**  
![alt text](for_md/for_second_stage/image-20.png)  
**אחרי הרצת השאילתא שוב קומיט ואז רולבק**  
![alt text](for_md/for_second_stage/image-21.png)  


## שני

**תיאור**: הוספת עובד חדש
**לפני הוספת עובד 4000**  
![alt text](for_md/for_second_stage/image-22.png)  

**אחרי הוספת עובד 4000**  
![alt text](for_md/for_second_stage/image-23.png)   

**אחרי רולבק**  
![alt text](for_md/for_second_stage/image-24.png)    

**אחרי הרצת השאילתא שוב קומיט ואז רולבק**  
![alt text](for_md/for_second_stage/image-25.png)  



### שלישי  
**תיאור**: אם כתוב STREET  מקצר אותו לST. 

**לפני שקיצרתי את הכתובת**    
![alt text](for_md/for_second_stage/image-26.png)  

**אחרי שקיצרתי את הכתובת**  
![alt text](for_md/for_second_stage/image-27.png)  



**אחרי רולבק**  
![alt text](for_md/for_second_stage/image-30.png)  

**אחרי הרצת השאילתא שוב קומיט ואז רולבק**  
![alt text](for_md/for_second_stage/image-31.png)

# שלב-ג

## אינטגרציה-ומבטים  
**מטרה**:  
בשלב זה ביצענו אינטגרציה עם מאגר מידע נוסף המתאר פעילות ציוד ואנשים במתחם חדרי הכושר.  
המטרה הייתה לחלץ את המבנה הנתוני מתוך קובץ גיבוי, לזהות טבלאות וישויות חדשות, לבנות תרשימים תואמים (DSD ו־ERD), ולהתחיל בהגדרת מבטים וניתוחים.

---

## קוד חילוץ מבנה הנתונים (DSD)  
לצורך התיעוד הטכני של שלב זה, כתבנו סקריפט פייתון (`extract_dsd.py`) שעובר על קובץ הגיבוי ומפיק ממנו את מבנה טבלאות בסיס הנתונים בצורה טקסטואלית.  
הקוד סורק הגדרות מתוך שאילתות `CREATE TABLE`, מזהה את שמות הטבלאות, העמודות וסוגי הנתונים, ומהן יצרנו את התרשימים (DSD ו־ERD).

---

## פלט הקוד – תרשים מבנה בסיס הנתונים  
<img src="שלב_ג/extracted_DSD.png" width="700"/>
התרשים נוצר אוטומטית על ידי הסקריפט, וממחיש בצורה גרפית את מבנה המערכת כפי שהופק מקובץ הגיבוי.

---

## תרשים ישויות ויחסים (ERD)  
<img src="שלב_ג/extracted_ERD.png" width="700"/>
התרשים נבנה על בסיס פלט הקוד, והוא מציג קשרים היררכיים, אילוצים בין טבלאות (כגון ירושה והרכבה), ואת ההיגיון העסקי של המערכת.

### החלטות

1. שמירת כל הנתונים שקשורים לperson שישאר שם
2. שmaintence worker יירש מperson ולא מworker כי זה גם יכול להיות freelance
3. כיון שכל האנשים עם אותו id בשתי הבסיס נתונים זה אנשים אחרים שיניתי לבסיס נתונים השני את הID(בכל הטבלאות)
4. כיון שמסובך לחבר כניסה לאותה יציאה בגישה למכשירים נחבר אותם לאותו טבלה שיהיה בה את הכניסה והיצאה של אותו שימוש.
     
<img src="שלב_ג/combined_ERD.png" width="700"/>  

## מבטים ושאילתות 

### מבט ראשון - כל המשכורות של כל סוגי העובדים  


<img src="שלב_ג/view_1.jpg" width="700"/>  

#### שאילתא 1   


<img src="שלב_ג//query_1_view_1.jpg" width="700"/>   


#### שאילתא 2   

<img src="שלב_ג//query_2_view_1.jpg" width="700"/>   



### מבט שני -

<img src="שלב_ג/view_2.png" width="700"/>  

#### שאילתא 1   

<img src="שלב_ג//query_1_view_2.jpg" width="700"/>   


#### שאילתא 2  

<img src="שלב_ג//query_2_view_2.jpg" width="700"/>   


