--
-- PostgreSQL database dump
--

\restrict Zp2kJmedbR6zSLcX6CwI6VWLbmyOsuh6Gaby9NyO6pXW9Sc5rcAQeWL241oi1XV

-- Dumped from database version 15.14 (Debian 15.14-1.pgdg13+1)
-- Dumped by pg_dump version 15.14 (Debian 15.14-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: calculate_hourly_worker_salary(integer, date); Type: FUNCTION; Schema: public; Owner: yehuda
--

CREATE FUNCTION public.calculate_hourly_worker_salary(p_worker_pid integer, p_month_year date) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.calculate_hourly_worker_salary(p_worker_pid integer, p_month_year date) OWNER TO yehuda;

--
-- Name: check_active_member_on_entry(); Type: FUNCTION; Schema: public; Owner: yehuda
--

CREATE FUNCTION public.check_active_member_on_entry() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_is_active BOOLEAN;
BEGIN
    SELECT isactive INTO v_is_active
    FROM public.member
    WHERE personid = NEW.personid;

    -- בדיקה והרמת חריגה
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Person with ID % is not a registered member.', NEW.personid;
    END IF;

    IF v_is_active IS FALSE THEN
        RAISE EXCEPTION 'Member with ID % is not active. Entry denied.', NEW.personid;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_active_member_on_entry() OWNER TO yehuda;

--
-- Name: fn_checkin(integer, integer, integer, integer, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: yehuda
--

CREATE FUNCTION public.fn_checkin(p_personid integer, p_deviceid integer, p_zoneid integer, p_gymid integer, p_entrytime timestamp without time zone DEFAULT now()) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- preflight: device must be registered to this zone/gym
  PERFORM 1
  FROM accessdevice
  WHERE deviceid = p_deviceid
    AND zoneid   = p_zoneid
    AND gymid    = p_gymid;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Device % is not registered to zone % in gym %',
      p_deviceid, p_zoneid, p_gymid
      USING ERRCODE = 'foreign_key_violation';
  END IF;

  -- prevent duplicate open session
  IF EXISTS (
    SELECT 1 FROM entryexit
    WHERE personid = p_personid
      AND deviceid = p_deviceid
      AND zoneid   = p_zoneid
      AND gymid    = p_gymid
      AND exittime IS NULL
  ) THEN
    RAISE EXCEPTION 'Open session already exists for person % on device % zone % gym %',
      p_personid, p_deviceid, p_zoneid, p_gymid;
  END IF;

  INSERT INTO entryexit(personid, deviceid, zoneid, gymid, entrytime)
  VALUES (p_personid, p_deviceid, p_zoneid, p_gymid, p_entrytime);
END;
$$;


ALTER FUNCTION public.fn_checkin(p_personid integer, p_deviceid integer, p_zoneid integer, p_gymid integer, p_entrytime timestamp without time zone) OWNER TO yehuda;

--
-- Name: get_active_repairs(timestamp without time zone, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: yehuda
--

CREATE FUNCTION public.get_active_repairs(p_start_date timestamp without time zone, p_end_date timestamp without time zone, OUT p_repairs_cursor refcursor) RETURNS refcursor
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


ALTER FUNCTION public.get_active_repairs(p_start_date timestamp without time zone, p_end_date timestamp without time zone, OUT p_repairs_cursor refcursor) OWNER TO yehuda;

--
-- Name: register_new_member(integer, character varying, character varying, date, character varying, character varying, numeric, character varying, boolean); Type: PROCEDURE; Schema: public; Owner: yehuda
--

CREATE PROCEDURE public.register_new_member(IN p_pid integer, IN p_firstname character varying, IN p_lastname character varying, IN p_dateofb date, IN p_email character varying DEFAULT NULL::character varying, IN p_address character varying DEFAULT NULL::character varying, IN p_phone numeric DEFAULT NULL::numeric, IN p_membership_type character varying DEFAULT NULL::character varying, IN p_is_active boolean DEFAULT true)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- טיפול בחריגה עבור משתמש קיים
    IF EXISTS (SELECT 1 FROM public.person WHERE pid = p_pid) THEN
        RAISE EXCEPTION 'A person with PID % already exists.', p_pid;
    END IF;

    -- פקודות DML (INSERT)
    INSERT INTO public.person(pid, dateofb, firstname, lastname, email, address, phone)
    VALUES (p_pid, p_dateofb, p_firstname, p_lastname, p_email, p_address, p_phone);

    INSERT INTO public.member(personid, memberstartdate, membershiptype, isactive)
    VALUES (p_pid, CURRENT_DATE, p_membership_type, p_is_active);

    RAISE NOTICE 'New member % % with membership type % registered successfully!', p_firstname, p_lastname, p_membership_type;

END;
$$;


ALTER PROCEDURE public.register_new_member(IN p_pid integer, IN p_firstname character varying, IN p_lastname character varying, IN p_dateofb date, IN p_email character varying, IN p_address character varying, IN p_phone numeric, IN p_membership_type character varying, IN p_is_active boolean) OWNER TO yehuda;

--
-- Name: update_expired_memberships(); Type: PROCEDURE; Schema: public; Owner: yehuda
--

CREATE PROCEDURE public.update_expired_memberships()
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_today       DATE := CURRENT_DATE;
    v_expire_date DATE;
    member_record RECORD;  -- declare the loop record
BEGIN
    RAISE NOTICE 'Starting to update expired memberships...';

    FOR member_record IN
        SELECT personid, memberstartdate, membershiptype
        FROM public.member
        WHERE isactive = TRUE
    LOOP
        -- compute expire date; cast to DATE
        v_expire_date :=
            CASE member_record.membershiptype
                WHEN 'Monthly'   THEN (member_record.memberstartdate + INTERVAL '1 month')::date
                WHEN 'Quarterly' THEN (member_record.memberstartdate + INTERVAL '3 months')::date
                WHEN 'Annual'    THEN (member_record.memberstartdate + INTERVAL '1 year')::date
                ELSE NULL
            END;

        IF v_expire_date IS NULL THEN
            CONTINUE; -- unsupported type
        END IF;

        IF v_today >= v_expire_date THEN
            UPDATE public.member
            SET isactive = FALSE
            WHERE personid = member_record.personid
              AND isactive = TRUE;

            RAISE NOTICE 'Membership for person ID % expired. Status updated to inactive.', member_record.personid;
        END IF;
    END LOOP;

    RAISE NOTICE 'Finished updating memberships.';
END;
$$;


ALTER PROCEDURE public.update_expired_memberships() OWNER TO yehuda;

--
-- Name: update_worker_shift_count(); Type: FUNCTION; Schema: public; Owner: yehuda
--

CREATE FUNCTION public.update_worker_shift_count() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- עדכון מונה המשמרות של העובד
    UPDATE public.worker
    SET total_shifts = (SELECT COUNT(*) FROM public.shift WHERE pid = NEW.pid)
    WHERE pid = NEW.pid;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_worker_shift_count() OWNER TO yehuda;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accessdevice; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.accessdevice (
    deviceid integer NOT NULL,
    zoneid integer NOT NULL,
    gymid integer NOT NULL,
    devicetype character varying(50) NOT NULL
);


ALTER TABLE public.accessdevice OWNER TO yehuda;

--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    username text NOT NULL,
    password_hash text NOT NULL,
    personid integer NOT NULL
);


ALTER TABLE public.auth_user OWNER TO yehuda;

--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: yehuda
--

CREATE SEQUENCE public.auth_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_user_id_seq OWNER TO yehuda;

--
-- Name: auth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yehuda
--

ALTER SEQUENCE public.auth_user_id_seq OWNED BY public.auth_user.id;


--
-- Name: entryexit; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.entryexit (
    personid integer NOT NULL,
    deviceid integer NOT NULL,
    zoneid integer NOT NULL,
    gymid integer NOT NULL,
    entrytime timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    exittime timestamp without time zone,
    CONSTRAINT valid_entry_time CHECK ((entrytime <= CURRENT_TIMESTAMP))
);


ALTER TABLE public.entryexit OWNER TO yehuda;

--
-- Name: freelance; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.freelance (
    pid integer NOT NULL
);


ALTER TABLE public.freelance OWNER TO yehuda;

--
-- Name: hourly; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.hourly (
    salaryph numeric(6,2) NOT NULL,
    bonus numeric(10,2) NOT NULL,
    overtimerate numeric(5,2) NOT NULL,
    pid integer NOT NULL
);


ALTER TABLE public.hourly OWNER TO yehuda;

--
-- Name: person; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.person (
    pid integer NOT NULL,
    dateofb date NOT NULL,
    firstname character varying(20) NOT NULL,
    lastname character varying(20) NOT NULL,
    email character varying(20),
    address character varying(20),
    phone numeric(10,0)
);


ALTER TABLE public.person OWNER TO yehuda;

--
-- Name: serves; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.serves (
    servicedateb date NOT NULL,
    servicedatee date NOT NULL,
    contract character varying(20) NOT NULL,
    price integer NOT NULL,
    servicename character varying(20) NOT NULL,
    pid integer NOT NULL
);


ALTER TABLE public.serves OWNER TO yehuda;

--
-- Name: services; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.services (
    servicename character varying(20) NOT NULL,
    equipmentrequired character varying(20) NOT NULL
);


ALTER TABLE public.services OWNER TO yehuda;

--
-- Name: worker; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.worker (
    job character varying(20) NOT NULL,
    contract character varying(500) NOT NULL,
    dateofeployment date NOT NULL,
    pid integer NOT NULL,
    total_shifts integer DEFAULT 0
);


ALTER TABLE public.worker OWNER TO yehuda;

--
-- Name: financial_view; Type: VIEW; Schema: public; Owner: yehuda
--

CREATE VIEW public.financial_view AS
 SELECT p.pid,
    p.firstname,
    p.lastname,
    s.servicename,
    sv.price,
    sv.servicedateb,
    sv.servicedatee,
    w.job,
    h.salaryph,
    h.overtimerate,
        CASE
            WHEN (f.pid IS NOT NULL) THEN true
            ELSE false
        END AS is_freelance,
        CASE
            WHEN (h.pid IS NOT NULL) THEN true
            ELSE false
        END AS is_hourly_worker
   FROM (((((public.person p
     LEFT JOIN public.worker w ON ((p.pid = w.pid)))
     LEFT JOIN public.hourly h ON ((w.pid = h.pid)))
     LEFT JOIN public.freelance f ON ((p.pid = f.pid)))
     LEFT JOIN public.serves sv ON ((f.pid = sv.pid)))
     LEFT JOIN public.services s ON (((sv.servicename)::text = (s.servicename)::text)));


ALTER TABLE public.financial_view OWNER TO yehuda;

--
-- Name: gym; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.gym (
    gymid integer NOT NULL,
    name character varying(100) NOT NULL,
    gymlocation character varying(255) NOT NULL
);


ALTER TABLE public.gym OWNER TO yehuda;

--
-- Name: maintenanceworker; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.maintenanceworker (
    personid integer NOT NULL,
    contactinfo character varying(100) NOT NULL,
    hiredate date NOT NULL,
    CONSTRAINT valid_contact CHECK ((((contactinfo)::text ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text) OR ((contactinfo)::text ~ '^\+?[0-9]{10,15}$'::text)))
);


ALTER TABLE public.maintenanceworker OWNER TO yehuda;

--
-- Name: member; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.member (
    personid integer NOT NULL,
    memberstartdate date NOT NULL,
    membershiptype character varying(50) NOT NULL,
    isactive boolean DEFAULT true,
    CONSTRAINT member_membershiptype_check CHECK (((membershiptype)::text = ANY (ARRAY[('Monthly'::character varying)::text, ('Annual'::character varying)::text, ('Quarterly'::character varying)::text, ('Daily'::character varying)::text, ('Personal Training'::character varying)::text])))
);


ALTER TABLE public.member OWNER TO yehuda;

--
-- Name: monthly; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.monthly (
    "vecationDays" double precision,
    "salaryPM" double precision,
    benefits_package text,
    "pId" bigint
);


ALTER TABLE public.monthly OWNER TO yehuda;

--
-- Name: repair; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.repair (
    personid integer NOT NULL,
    date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deviceid integer NOT NULL,
    zoneid integer NOT NULL,
    gymid integer NOT NULL,
    specialnotes character varying(255),
    servicetype character varying(50) NOT NULL,
    CONSTRAINT repair_servicetype_check CHECK (((servicetype)::text = ANY (ARRAY[('Urgent Repair'::character varying)::text, ('Maintenance'::character varying)::text, ('Upgrade'::character varying)::text, ('Inspection'::character varying)::text, ('Replacement'::character varying)::text]))),
    CONSTRAINT valid_repair_date CHECK ((date <= CURRENT_TIMESTAMP))
);


ALTER TABLE public.repair OWNER TO yehuda;

--
-- Name: zone; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.zone (
    zoneid integer NOT NULL,
    gymid integer NOT NULL,
    zonetype character varying(50) NOT NULL,
    onlyformembers boolean DEFAULT false,
    isaccessible boolean DEFAULT true
);


ALTER TABLE public.zone OWNER TO yehuda;

--
-- Name: operations_view; Type: VIEW; Schema: public; Owner: yehuda
--

CREATE VIEW public.operations_view AS
 SELECT ad.deviceid,
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
   FROM ((((public.accessdevice ad
     JOIN public.zone z ON (((ad.zoneid = z.zoneid) AND (ad.gymid = z.gymid))))
     JOIN public.gym g ON ((z.gymid = g.gymid)))
     LEFT JOIN public.entryexit ee ON (((ad.deviceid = ee.deviceid) AND (ad.zoneid = ee.zoneid) AND (ad.gymid = ee.gymid))))
     LEFT JOIN public.repair r ON (((ad.deviceid = r.deviceid) AND (ad.zoneid = r.zoneid) AND (ad.gymid = r.gymid))));


ALTER TABLE public.operations_view OWNER TO yehuda;

--
-- Name: shift; Type: TABLE; Schema: public; Owner: yehuda
--

CREATE TABLE public.shift (
    pid integer NOT NULL,
    date date NOT NULL,
    clock_in time without time zone NOT NULL,
    clock_out time without time zone NOT NULL
);


ALTER TABLE public.shift OWNER TO yehuda;

--
-- Name: auth_user id; Type: DEFAULT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.auth_user ALTER COLUMN id SET DEFAULT nextval('public.auth_user_id_seq'::regclass);


--
-- Name: accessdevice accessdevice_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.accessdevice
    ADD CONSTRAINT accessdevice_pkey PRIMARY KEY (deviceid, zoneid, gymid);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: entryexit entryrecord_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.entryexit
    ADD CONSTRAINT entryrecord_pkey PRIMARY KEY (personid, deviceid, zoneid, gymid, entrytime);


--
-- Name: freelance freelance_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.freelance
    ADD CONSTRAINT freelance_pkey PRIMARY KEY (pid);


--
-- Name: gym gym_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.gym
    ADD CONSTRAINT gym_pkey PRIMARY KEY (gymid);


--
-- Name: hourly hourly_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.hourly
    ADD CONSTRAINT hourly_pkey PRIMARY KEY (pid);


--
-- Name: maintenanceworker maintenanceworker_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.maintenanceworker
    ADD CONSTRAINT maintenanceworker_pkey PRIMARY KEY (personid);


--
-- Name: member member_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.member
    ADD CONSTRAINT member_pkey PRIMARY KEY (personid);


--
-- Name: person person_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.person
    ADD CONSTRAINT person_pkey PRIMARY KEY (pid);


--
-- Name: repair repair_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.repair
    ADD CONSTRAINT repair_pkey PRIMARY KEY (personid, date, deviceid, zoneid, gymid);


--
-- Name: serves serves_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.serves
    ADD CONSTRAINT serves_pkey PRIMARY KEY (servicename, pid);


--
-- Name: services services_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_pkey PRIMARY KEY (servicename);


--
-- Name: shift shift_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.shift
    ADD CONSTRAINT shift_pkey PRIMARY KEY (pid, date);


--
-- Name: worker worker_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.worker
    ADD CONSTRAINT worker_pkey PRIMARY KEY (pid);


--
-- Name: zone zone_pkey; Type: CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.zone
    ADD CONSTRAINT zone_pkey PRIMARY KEY (zoneid, gymid);


--
-- Name: idx_auth_user_personid; Type: INDEX; Schema: public; Owner: yehuda
--

CREATE INDEX idx_auth_user_personid ON public.auth_user USING btree (personid);


--
-- Name: idx_repair_date; Type: INDEX; Schema: public; Owner: yehuda
--

CREATE INDEX idx_repair_date ON public.repair USING btree (date);


--
-- Name: idx_repair_device; Type: INDEX; Schema: public; Owner: yehuda
--

CREATE INDEX idx_repair_device ON public.repair USING btree (deviceid, zoneid, gymid);


--
-- Name: idx_repair_person; Type: INDEX; Schema: public; Owner: yehuda
--

CREATE INDEX idx_repair_person ON public.repair USING btree (personid);


--
-- Name: entryexit check_member_status_trigger; Type: TRIGGER; Schema: public; Owner: yehuda
--

CREATE TRIGGER check_member_status_trigger BEFORE INSERT ON public.entryexit FOR EACH ROW EXECUTE FUNCTION public.check_active_member_on_entry();


--
-- Name: shift update_shifts_after_shift_change; Type: TRIGGER; Schema: public; Owner: yehuda
--

CREATE TRIGGER update_shifts_after_shift_change AFTER INSERT OR UPDATE ON public.shift FOR EACH ROW EXECUTE FUNCTION public.update_worker_shift_count();


--
-- Name: accessdevice accessdevice_zoneid_gymid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.accessdevice
    ADD CONSTRAINT accessdevice_zoneid_gymid_fkey FOREIGN KEY (zoneid, gymid) REFERENCES public.zone(zoneid, gymid) ON DELETE CASCADE;


--
-- Name: auth_user auth_user_personid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_personid_fkey FOREIGN KEY (personid) REFERENCES public.person(pid) ON DELETE CASCADE;


--
-- Name: entryexit entryrecord_deviceid_zoneid_gymid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.entryexit
    ADD CONSTRAINT entryrecord_deviceid_zoneid_gymid_fkey FOREIGN KEY (deviceid, zoneid, gymid) REFERENCES public.accessdevice(deviceid, zoneid, gymid);


--
-- Name: hourly hourly_pid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.hourly
    ADD CONSTRAINT hourly_pid_fkey FOREIGN KEY (pid) REFERENCES public.worker(pid);


--
-- Name: repair repair_deviceid_zoneid_gymid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.repair
    ADD CONSTRAINT repair_deviceid_zoneid_gymid_fkey FOREIGN KEY (deviceid, zoneid, gymid) REFERENCES public.accessdevice(deviceid, zoneid, gymid);


--
-- Name: serves serves_pid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.serves
    ADD CONSTRAINT serves_pid_fkey FOREIGN KEY (pid) REFERENCES public.freelance(pid);


--
-- Name: serves serves_servicename_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.serves
    ADD CONSTRAINT serves_servicename_fkey FOREIGN KEY (servicename) REFERENCES public.services(servicename);


--
-- Name: shift shift_pid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yehuda
--

ALTER TABLE ONLY public.shift
    ADD CONSTRAINT shift_pid_fkey FOREIGN KEY (pid) REFERENCES public.hourly(pid);


--
-- PostgreSQL database dump complete
--

\unrestrict Zp2kJmedbR6zSLcX6CwI6VWLbmyOsuh6Gaby9NyO6pXW9Sc5rcAQeWL241oi1XV

