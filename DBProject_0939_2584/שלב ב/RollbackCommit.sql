
-- the first rollback and commit where i deleted all the services that were given before 10/7/2023


select * from serves
BEGIN;     
delete from serves where servicedatee<'2023-07-10';
select * from serves;
rollback;
select * from serves;
delete from serves where servicedatee<'2023-07-10';
commit ;
rollback ;
select * from serves





--the second rollback and commit example where i inserted a new person to the database (pid 4000)

select * from person order by pid desc
BEGIN;     
INSERT INTO person(pId, DateOfB, firstName, lastName, email, address, phone)
VALUES 
(4000, '1990-01-15', 'חחחחחח',    'חשבת?',   'john.s@example.com',  '123MainSt', 1234567890);
select * from person order by pid desc;
rollback;
select * from person order by pid desc
INSERT INTO person(pId, DateOfB, firstName, lastName, email, address, phone)
VALUES 
(4000, '1990-01-15', 'חחחחחח',    'חשבת?',   'john.s@example.com',  '123MainSt', 1234567890);
commit ;
rollback ;
select * from person order by pid desc

--the third rollback and commit example where every time an address has the "STREET"  in it a change it to it's abbreviation "St."



select pid,address from person order by pid desc
BEGIN;     
UPDATE person
SET    address = REGEXP_REPLACE(address,
                                '\ySTREET\y',   -- גבולות‑מילה
                                'St.',
                                'i')            -- i = חסר‑רגישות־רישיות
WHERE  address ~* '\ySTREET\y' ;
select pid,address from person order by pid desc
rollback;
select pid,address from person order by pid desc
SET    address = REGEXP_REPLACE(address,
                                '\ySTREET\y',   -- גבולות‑מילה
                                'St.',
                                'i')            -- i = חסר‑רגישות־רישיות
WHERE  address ~* '\ySTREET\y' ; 
commit ;
rollback ;
select pid,address from person order by pid desc
