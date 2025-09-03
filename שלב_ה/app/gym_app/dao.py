from typing import List, Tuple, Optional, Any
from datetime import date
from .config import TABLES, COLUMNS, PAGE_SIZE

def _t(n): return TABLES[n]
def _c(n): return COLUMNS[n]

# -------------------- PERSON --------------------
def list_persons(conn, search="", page=1, page_size=PAGE_SIZE):
    t=_t("person"); cols=[_c("person.pid"),_c("person.firstname"),_c("person.lastname"),
        _c("person.dateofb"),_c("person.email"),_c("person.address"),_c("person.phone")]
    where=""; params=[]
    if search:
        where=f"WHERE {cols[1]} ILIKE %s OR {cols[2]} ILIKE %s OR {cols[4]} ILIKE %s"
        like=f"%{search}%"; params=[like,like,like]
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {t} {where}", params); total=cur.fetchone()[0]
    offset=(page-1)*page_size
    with conn.cursor() as cur:
        cur.execute(f"SELECT {', '.join(cols)} FROM {t} {where} ORDER BY {cols[0]} LIMIT %s OFFSET %s",
                    params+[page_size,offset])
        rows=cur.fetchall()
    return rows,total

def create_person(conn, pid, firstname, lastname, dateofb, email, address, phone):
    t=_t("person"); cols=(_c("person.pid"),_c("person.firstname"),_c("person.lastname"),
        _c("person.dateofb"),_c("person.email"),_c("person.address"),_c("person.phone"))
    with conn.cursor() as cur:
        cur.execute(f"INSERT INTO {t} ({', '.join(cols)}) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (pid,firstname,lastname,dateofb,email,address,phone))

def update_person(conn, pid, firstname, lastname, dateofb, email, address, phone):
    t=_t("person"); c=COLUMNS
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE {t} SET {c['person.firstname']}=%s,{c['person.lastname']}=%s,"
            f"{c['person.dateofb']}=%s,{c['person.email']}=%s,{c['person.address']}=%s,"
            f"{c['person.phone']}=%s WHERE {c['person.pid']}=%s",
            (firstname,lastname,dateofb,email,address,phone,pid))

def delete_person(conn, pid):
    t=_t("person")
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {t} WHERE {_c('person.pid')}=%s",(pid,))

# -------------------- MEMBER --------------------
def list_members(conn, search="", page=1, page_size=PAGE_SIZE):
    t_p=_t("person"); t_m=_t("member"); p=COLUMNS; where=""; params=[]
    if search:
        where=f"WHERE p.{p['person.firstname']} ILIKE %s OR p.{p['person.lastname']} ILIKE %s"
        like=f'%{search}%'; params=[like,like]
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {t_m} m JOIN {t_p} p ON p.{p['person.pid']}=m.{p['member.personid']} {where}", params)
        total=cur.fetchone()[0]
    offset=(page-1)*page_size
    sql=(
        f"SELECT p.{p['person.pid']}, p.{p['person.firstname']}, p.{p['person.lastname']},"
        f"       m.{p['member.membershiptype']}, m.{p['member.memberstartdate']}, m.{p['member.isactive']}"
        f"  FROM {t_m} m JOIN {t_p} p ON p.{p['person.pid']}=m.{p['member.personid']} {where}"
        f"  ORDER BY p.{p['person.pid']} LIMIT %s OFFSET %s"
    )
    with conn.cursor() as cur:
        cur.execute(sql, params+[page_size, offset]); rows=cur.fetchall()
    return rows,total

def upsert_member_via_proc(conn, pid, firstname, lastname, dateofb, email, address, phone, membershiptype, isactive):
    with conn.cursor() as cur:
        cur.execute("CALL register_new_member(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (pid,firstname,lastname,dateofb,email,address,phone,membershiptype,isactive))

def update_member(conn, personid, membershiptype, isactive):
    t=_t("member"); c=COLUMNS
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE {t} SET {c['member.membershiptype']}=%s,{c['member.isactive']}=%s "
            f"WHERE {c['member.personid']}=%s",
            (membershiptype,isactive,personid))

def delete_member(conn, personid):
    t=_t("member"); c=COLUMNS
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {t} WHERE {c['member.personid']}=%s",(personid,))

# -------------------- SHIFTS --------------------
def list_shifts(conn, search_pid=None, month=None, year=None, page=1, page_size=PAGE_SIZE):
    """
    מחזיר משמרות עם סינון שרת-צד (PID, חודש/שנה).
    אם search_pid אינו None — נשמרת מגבלה WHERE pid=%s כך שעובד שעתי יקבל רק את שלו.
    """
    t=_t("shift"); c=COLUMNS
    where_parts=[]; params=[]

    if search_pid is not None:
        where_parts.append(f"{c['shift.pid']}=%s")
        params.append(search_pid)

    if month is not None and year is not None:
        start=date(year, month, 1)
        next_year, next_month = (year+1,1) if month==12 else (year, month+1)
        end=date(next_year, next_month, 1)
        where_parts.append(f"{c['shift.date']} >= %s AND {c['shift.date']} < %s")
        params.extend([start,end])

    where_sql=("WHERE "+ " AND ".join(where_parts)) if where_parts else ""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {t} {where_sql}", params)
        total=cur.fetchone()[0]

    offset=(page-1)*page_size
    sql=(
        f"SELECT {c['shift.pid']},{c['shift.date']},{c['shift.clock_in']},{c['shift.clock_out']}"
        f"  FROM {t} {where_sql}"
        f"  ORDER BY {c['shift.pid']},{c['shift.date']} NULLS LAST,{c['shift.clock_in']}"
        f"  LIMIT %s OFFSET %s"
    )
    with conn.cursor() as cur:
        cur.execute(sql, params+[page_size, offset])
        rows=cur.fetchall()
    return rows,total

def create_shift(conn, pid, shift_date, clock_in, clock_out):
    t=_t("shift"); c=COLUMNS; cols=[c['shift.pid'],c['shift.date'],c['shift.clock_in'],c['shift.clock_out']]
    with conn.cursor() as cur:
        cur.execute(f"INSERT INTO {t} ({', '.join(cols)}) VALUES (%s,%s,%s,%s)",
                    (pid,shift_date,clock_in,clock_out))

def update_shift(conn, pid, shift_date, old_clock_in, clock_in, clock_out):
    t=_t("shift"); c=COLUMNS
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE {t} SET {c['shift.clock_in']}=%s,{c['shift.clock_out']}=%s "
            f"WHERE {c['shift.pid']}=%s AND {c['shift.date']}=%s AND {c['shift.clock_in']}=%s",
            (clock_in,clock_out,pid,shift_date,old_clock_in))

def delete_shift(conn, pid, shift_date, clock_in):
    t=_t("shift"); c=COLUMNS
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {t} WHERE {c['shift.pid']}=%s AND {c['shift.date']}=%s AND {c['shift.clock_in']}=%s",
            (pid,shift_date,clock_in))

# -------------------- REPORTS & PROCS --------------------
def hours_by_month(conn, month:int, year:int):
    t_p=_t("person"); t_s=_t("shift"); c=COLUMNS
    start=date(year,month,1); end=date(year+(1 if month==12 else 0),(1 if month==12 else month+1),1)
    sql=(
        f"SELECT p.{c['person.firstname']}, p.{c['person.lastname']}, "
        f"       SUM(EXTRACT(EPOCH FROM ({c['shift.clock_out']} - {c['shift.clock_in']})))/3600 AS total_hours "
        f"  FROM {t_p} p JOIN {t_s} s ON p.{c['person.pid']}=s.{c['shift.pid']} "
        f" WHERE s.{c['shift.date']} >= %s AND s.{c['shift.date']} < %s "
        f" GROUP BY p.{c['person.pid']}, p.{c['person.firstname']}, p.{c['person.lastname']} "
        f" ORDER BY total_hours DESC"
    )
    with conn.cursor() as cur:
        cur.execute(sql,(start,end)); return cur.fetchall()

def most_expensive_service(conn):
    t=_t("serves"); c=COLUMNS
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {c['serves.servicename']} AS name, SUM({c['serves.price']}) AS total "
            f"FROM {t} GROUP BY {c['serves.servicename']} ORDER BY total DESC LIMIT 1")
        return cur.fetchall()

def proc_update_expired(conn):
    with conn.cursor() as cur:
        cur.execute("CALL update_expired_memberships()")

# -------------------- AUTH --------------------
def authenticate_user(conn, username: str, password: str):
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, personid, role FROM authenticate_user(%s,%s)", (username, password))
        row=cur.fetchone()
        return row

def is_hourly_pid(conn, pid: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM hourly WHERE pid = %s)", (pid,))
        return cur.fetchone()[0]
