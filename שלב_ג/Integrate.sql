ALTER TABLE person RENAME TO  person_1;
ALTER TABLE worker RENAME TO  worker_1;
ALTER TABLE hourly RENAME TO  hourly_1;
ALTER TABLE monthly RENAME TO  monthly_1;
ALTER TABLE freelance RENAME TO  freelance_1;
ALTER TABLE services RENAME TO  services_1;
ALTER TABLE serves RENAME TO  serves_1;
ALTER TABLE shift RENAME TO  shift_1;
commit;

-- 1. Rename columns
ALTER TABLE person
  RENAME COLUMN personid    TO pid;
  ALTER TABLE person
  RENAME COLUMN dateofbirth TO dateofb;

-- 2. Shrink first/last name to 20 chars
ALTER TABLE person
  ALTER COLUMN firstname TYPE VARCHAR(20);
  ALTER TABLE person
  ALTER COLUMN lastname  TYPE VARCHAR(20);

-- 3. Add the three new columns
ALTER TABLE person
  ADD COLUMN email   VARCHAR(20);
  ALTER TABLE person
  ADD COLUMN address VARCHAR(20);
  ALTER TABLE person
  ADD COLUMN phone   NUMERIC(10);



ALTER TABLE person_1
ALTER COLUMN email DROP  not null;
commit;

ALTER TABLE person_1
ALTER COLUMN address DROP  not null;
commit;

ALTER TABLE person_1
ALTER COLUMN phone DROP  not null;
commit;




SELECT count(*) FROM person;
SELECT count(*) FROM person_1;
SELECT * FROM person;


UPDATE person
   SET pid = pid + 10000;
update entryrecord 
  set personid = personid+10000;
  update exitrecord 
  set personid = personid+10000; 
ALTER TABLE repair
DROP CONSTRAINT repair_personid_fkey;
  update maintenanceworker 
  set personid = personid+10000;
select * from exitrecord;
 update repair 
  set personid = personid+10000;
  update member 
  set personid = personid+10000;
select * from zone;
commit;

insert into person_1 
select pid, dateofb, firstname, lastname, email, address, phone
from person p
where p.pid not in (select pid from person_1);
select * from exitrecord;
commit;
select * from person_1 order by pid desc;


delete from "entry record";
drop table public."entry record";
commit;
SELECT COUNT(*) FROM "entry record";
SELECT COUNT(*) FROM entryrecord;
ALTER TABLE entry  RENAME TO  person_1;

drop table "entry record";
commit;

drop table "exitrecord";
commit;

ALTER TABLE IF EXISTS public.entryrecord
    ADD COLUMN exittime timestamp without time zone;
commit;

begin;

UPDATE entryrecord
SET exittime = entrytime +
    CASE
        -- כניסה ביום (06:00–22:00) → בין חצי שעה ל־4 שעות
        WHEN EXTRACT(HOUR FROM entrytime) BETWEEN 6 AND 21
            THEN (INTERVAL '1 minute' * (30 + floor(random() * 210))) 
            -- 30 עד 240 דקות
        -- כניסה בלילה (22:00–05:59) → בין 5 ל־60 דקות
        ELSE (INTERVAL '1 minute' * (5 + floor(random() * 55))) 
            -- 5 עד 60 דקות
    END
WHERE exittime IS NULL;

ALTER TABLE entryrecord RENAME TO  entryexit;

COMMIT;


 drop table person
ALTER TABLE person_1 RENAME TO  person;
ALTER TABLE worker_1 RENAME TO  worker;
ALTER TABLE hourly_1 RENAME TO  hourly;
ALTER TABLE monthly_1 RENAME TO  monthly;
ALTER TABLE freelance_1 RENAME TO  freelance;
ALTER TABLE services_1 RENAME TO  services;
ALTER TABLE serves_1 RENAME TO  serves;
ALTER TABLE shift_1 RENAME TO  shift;
commit;


