# -*- coding: utf-8 -*-
"""
DAO layer for Gym Management App (Tkinter + PostgreSQL).
Each write commits. Errors are raised as Python exceptions for the UI to show nicely.
"""

from __future__ import annotations

from typing import Optional, Tuple, List, Dict
from datetime import date, datetime
from psycopg2 import sql

# =========================
#  Authentication & Users
# =========================

def authenticate_user(conn, username: str, password: str) -> Optional[Tuple[int, int, str]]:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM authenticate_user(%s, %s)", (username, password))
        row = cur.fetchone()
    return row if row else None


def change_password_by_pid(conn, pid: int, current_password: str, new_password: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT change_password_by_pid(%s, %s, %s)",
            (pid, current_password, new_password),
        )
        ok = bool(cur.fetchone()[0])
    conn.commit()
    return ok


def admin_reset_password_by_pid(conn, pid: int) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT admin_reset_password_by_pid(%s)", (pid,))
    conn.commit()


def ensure_default_admin(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT ensure_default_admin()")
    conn.commit()


# =========================
#  Helpers (schema/validation)
# =========================

def _varchar_limits(conn, table: str) -> Dict[str, Optional[int]]:
    """
    Return {column: character_maximum_length or None} for a table.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            """,
            (table,),
        )
        return {name: maxlen for (name, maxlen) in cur.fetchall()}


def _validate_varchar_lengths(values: Dict[str, Optional[str]], limits: Dict[str, Optional[int]]):
    """
    Raise ValueError if any provided text value exceeds its varchar limit.
    """
    too_long = []
    for col, val in values.items():
        if val is None:
            continue
        maxlen = limits.get(col)
        if maxlen is not None and isinstance(val, str) and len(val) > maxlen:
            too_long.append(f"{col} (max {maxlen}, got {len(val)})")
    if too_long:
        raise ValueError("Text too long: " + ", ".join(too_long))


# =========================
#  Persons CRUD (paging)
# =========================

def person_exists(conn, pid: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM person WHERE pid=%s", (pid,))
        return cur.fetchone() is not None


def list_persons(
    conn,
    search: str = "",
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Tuple], int]:
    search = (search or "").strip()
    where = ""
    args: List = []
    if search:
        where = """WHERE (firstname ILIKE %s OR lastname ILIKE %s OR pid::text ILIKE %s)"""
        args = [f"%{search}%", f"%{search}%", f"%{search}%"]

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM person {where}", args)
        total = int(cur.fetchone()[0])

        offset = (max(1, page) - 1) * max(1, page_size)
        cur.execute(
            f"""
            SELECT pid, firstname, lastname, dateofb, email, address, phone
            FROM person
            {where}
            ORDER BY pid ASC
            LIMIT %s OFFSET %s
            """,
            args + [page_size, offset],
        )
        rows = cur.fetchall()
    return rows, total


def create_person(
    conn,
    pid: int,
    firstname: str,
    lastname: str,
    dateofb: date,
    email: Optional[str],
    address: Optional[str],
    phone: Optional[int],
) -> None:
    # 1) prevent duplicate PID (PK יפיל גם כך, אבל עדיף הודעה ידידותית)
    if person_exists(conn, pid):
        raise ValueError(f"PID {pid} already exists")

    # 2) length validation by schema limits
    limits = _varchar_limits(conn, "person")
    _validate_varchar_lengths(
        {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "address": address,
        },
        limits,
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO person(pid, dateofb, firstname, lastname, email, address, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (pid, dateofb, firstname, lastname, email, address, phone),
        )
    conn.commit()


def update_person(
    conn,
    pid: int,
    firstname: str,
    lastname: str,
    dateofb: date,
    email: Optional[str],
    address: Optional[str],
    phone: Optional[int],
) -> None:
    # validate varchar lengths
    limits = _varchar_limits(conn, "person")
    _validate_varchar_lengths(
        {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "address": address,
        },
        limits,
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE person
               SET firstname=%s, lastname=%s, dateofb=%s, email=%s, address=%s, phone=%s
             WHERE pid=%s
            """,
            (firstname, lastname, dateofb, email, address, phone, pid),
        )
        if cur.rowcount == 0:
            raise RuntimeError("Person not found or unchanged")
    conn.commit()


def delete_person(conn, pid: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM person WHERE pid=%s", (pid,))
        if cur.rowcount == 0:
            raise RuntimeError("Person not found")
    conn.commit()


# =========================
#  Members (join person)
# =========================

def list_members(
    conn,
    search: str = "",
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Tuple], int]:
    search = (search or "").strip()
    where = ""
    args: List = []
    if search:
        # FIX: filter on the CTE columns (joined), not on alias p.*
        where = """
        WHERE (firstname ILIKE %s OR lastname ILIKE %s OR pid::text ILIKE %s)
        """
        args = [f"%{search}%", f"%{search}%", f"%{search}%"]

    with conn.cursor() as cur:
        cur.execute(
            f"""
            WITH joined AS (
              SELECT p.pid, p.firstname, p.lastname,
                     m.membershiptype, m.memberstartdate, m.isactive
              FROM person p
              JOIN member m ON m.personid = p.pid
            )
            SELECT COUNT(*) FROM joined {where}
            """,
            args,
        )
        total = int(cur.fetchone()[0])

        offset = (max(1, page) - 1) * max(1, page_size)
        cur.execute(
            f"""
            WITH joined AS (
              SELECT p.pid, p.firstname, p.lastname,
                     m.membershiptype, m.memberstartdate, m.isactive
              FROM person p
              JOIN member m ON m.personid = p.pid
            )
            SELECT pid, firstname, lastname, membershiptype, memberstartdate, isactive
            FROM joined
            {where}
            ORDER BY pid ASC
            LIMIT %s OFFSET %s
            """,
            args + [page_size, offset],
        )
        rows = cur.fetchall()
    return rows, total


def upsert_member_via_proc(
    conn,
    pid: int,
    firstname: str,
    lastname: str,
    dateofb: Optional[date],
    email: Optional[str],
    address: Optional[str],
    phone: Optional[int],
    membershiptype: str,
    isactive: bool,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "CALL register_new_member(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (pid, firstname, lastname, dateofb, email, address, phone, membershiptype, isactive),
        )
    conn.commit()


def update_member(conn, pid: int, membershiptype: str, isactive: bool) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE member SET membershiptype=%s, isactive=%s WHERE personid=%s",
            (membershiptype, isactive, pid),
        )
        if cur.rowcount == 0:
            raise RuntimeError("Member row not found or unchanged")
    conn.commit()


def delete_member(conn, pid: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM member WHERE personid=%s", (pid,))
        if cur.rowcount == 0:
            raise RuntimeError("Member row not found")
    conn.commit()


# =========================
#  Shifts CRUD (with paging)
# =========================

def list_shifts(
    conn,
    search_pid: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Tuple], int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH filtered AS (
              SELECT pid, "date", clock_in, clock_out
              FROM shift
              WHERE (%s IS NULL OR pid = %s)
                AND (%s IS NULL OR EXTRACT(MONTH FROM "date") = %s)
                AND (%s IS NULL OR EXTRACT(YEAR  FROM "date") = %s)
            )
            SELECT COUNT(*) FROM filtered
            """,
            (search_pid, search_pid, month, month, year, year),
        )
        total = int(cur.fetchone()[0])

        offset = (max(1, page) - 1) * max(1, page_size)
        cur.execute(
            """
            WITH filtered AS (
              SELECT pid, "date", clock_in, clock_out
              FROM shift
              WHERE (%s IS NULL OR pid = %s)
                AND (%s IS NULL OR EXTRACT(MONTH FROM "date") = %s)
                AND (%s IS NULL OR EXTRACT(YEAR  FROM "date") = %s)
            )
            SELECT pid, "date", clock_in, clock_out
            FROM filtered
            ORDER BY "date" DESC, clock_in DESC
            LIMIT %s OFFSET %s
            """,
            (search_pid, search_pid, month, month, year, year, page_size, offset),
        )
        rows = cur.fetchall()
    return rows, total


def create_shift(conn, pid: int, sdate: date, clock_in: datetime, clock_out: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO shift(pid, "date", clock_in, clock_out) VALUES (%s, %s, %s, %s)',
            (pid, sdate, clock_in, clock_out),
        )
    conn.commit()


def update_shift(
    conn,
    pid: int,
    sdate: date,
    old_clock_in: datetime,
    new_clock_in: datetime,
    clock_out: datetime,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE shift SET clock_in=%s, clock_out=%s WHERE pid=%s AND "date"=%s AND clock_in=%s',
            (new_clock_in, clock_out, pid, sdate, old_clock_in),
        )
        if cur.rowcount == 0:
            raise RuntimeError("Shift not found or unchanged")
    conn.commit()


def delete_shift(conn, pid: int, sdate, clock_in) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'DELETE FROM shift WHERE pid=%s AND "date"=%s AND clock_in=%s',
            (pid, sdate, clock_in),
        )
        if cur.rowcount == 0:
            raise RuntimeError("Shift not found")
    conn.commit()


# =========================
#  Reports & Procedures
# =========================

def hours_by_month(conn, month: int, year: int) -> List[Tuple[str, str, float]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.firstname, p.lastname,
                   SUM(EXTRACT(EPOCH FROM (s.clock_out - s.clock_in))) / 3600 AS total_hours
            FROM person p
            JOIN shift s ON p.pid = s.pid
            WHERE EXTRACT(MONTH FROM s.date) = %s
              AND EXTRACT(YEAR  FROM s.date) = %s
            GROUP BY p.pid, p.firstname, p.lastname
            ORDER BY total_hours DESC
            """,
            (month, year),
        )
        return cur.fetchall()


def most_expensive_service(conn) -> List[Tuple[str, float]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH listoftotals AS (
              SELECT servicename, SUM(price) AS total
              FROM serves
              GROUP BY servicename
            )
            SELECT servicename AS most_expensive_service, total
            FROM listoftotals
            WHERE total = (SELECT MAX(total) FROM listoftotals)
            """
        )
        return cur.fetchall()


def proc_update_expired(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CALL update_expired_memberships()")
    conn.commit()


# ===========================================
#  Generic Admin Data Manager (whitelisted)
# ===========================================

ALLOWED_TABLES = [
    "person", "member", "worker", "hourly", "monthly", "freelance",
    "maintenanceworker", "gym", "accessdevice", "entryexit", "shift", "serves"
]


def list_allowed_tables() -> List[str]:
    return ALLOWED_TABLES[:]


def get_table_columns(conn, table: str) -> Tuple[List[Dict], List[str]]:
    if table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name,
                   data_type,
                   (is_nullable = 'YES') AS nullable,
                   column_default
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        cols = [
            {
                "name": name,
                "data_type": dt,
                "nullable": bool(nullable),
                "default": default,
            }
            for (name, dt, nullable, default) in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
             AND tc.table_name   = kcu.table_name
            WHERE tc.table_schema='public'
              AND tc.table_name=%s
              AND tc.constraint_type='PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """,
            (table,),
        )
        pk_cols = [r[0] for r in cur.fetchall()]

    return cols, pk_cols


def _is_text_type(dt: str) -> bool:
    return any(t in (dt or "").lower() for t in ["char", "text"])


def fetch_table_rows_advanced(
    conn,
    table: str,
    limit: int = 100,
    offset: int = 0,
    search_column: Optional[str] = None,
    search_value: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: str = "ASC",
) -> Tuple[List[Tuple], int, List[str], List[Dict], List[str]]:
    if table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    cols_meta, pk_cols = get_table_columns(conn, table)
    col_names = [c["name"] for c in cols_meta]

    where_sql = sql.SQL("")
    where_args: List = []
    if search_column and search_value and search_column in col_names:
        col_dt = next((c["data_type"] for c in cols_meta if c["name"] == search_column), "")
        if _is_text_type(col_dt):
            where_sql = sql.SQL("WHERE {} ILIKE %s").format(sql.Identifier(search_column))
            where_args.append(f"%{search_value}%")
        else:
            where_sql = sql.SQL("WHERE {} = %s").format(sql.Identifier(search_column))
            where_args.append(search_value)

    if sort_by and sort_by in col_names:
        direction = "DESC" if str(sort_dir).upper().startswith("D") else "ASC"
        order_sql = sql.SQL("ORDER BY {} {} NULLS LAST").format(
            sql.Identifier(sort_by), sql.SQL(direction)
        )
    else:
        order_cols = pk_cols if pk_cols else col_names[:1]
        order_sql = sql.SQL("ORDER BY {} NULLS LAST").format(
            sql.SQL(", ").join(sql.Identifier(c) for c in order_cols)
        )

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT COUNT(*) FROM {} {}").format(
                sql.Identifier(table), where_sql
            ),
            where_args,
        )
        total = int(cur.fetchone()[0])

        cur.execute(
            sql.SQL("SELECT {} FROM {} {} {} LIMIT %s OFFSET %s").format(
                sql.SQL(", ").join(sql.Identifier(c) for c in col_names),
                sql.Identifier(table),
                where_sql,
                order_sql,
            ),
            where_args + [limit, offset],
        )
        rows = cur.fetchall()

    return rows, total, col_names, cols_meta, pk_cols


def fetch_table_rows(conn, table: str, limit: int = 100, offset: int = 0) -> Tuple[List[Tuple], int, List[str]]:
    rows, total, col_names, _meta, _pk = fetch_table_rows_advanced(
        conn, table, limit=limit, offset=offset
    )
    return rows, total, col_names


def insert_row(conn, table: str, payload: Dict) -> None:
    if table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    cols_meta, _ = get_table_columns(conn, table)
    valid_cols = {c["name"] for c in cols_meta}
    data = {k: v for k, v in payload.items() if k in valid_cols}

    if not data:
        raise ValueError("No valid columns to insert")

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table),
                sql.SQL(", ").join(sql.Identifier(k) for k in data.keys()),
                sql.SQL(", ").join(sql.Placeholder() for _ in data.keys()),
            ),
            list(data.values()),
        )
    conn.commit()


def update_row(conn, table: str, payload: Dict, pk_values: Dict) -> None:
    if table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    cols_meta, pk_cols = get_table_columns(conn, table)
    if not pk_cols:
        raise ValueError("Table has no primary key; cannot update generically")

    valid_cols = {c["name"] for c in cols_meta}
    set_cols = [c for c in payload.keys() if c in valid_cols and c not in pk_cols]
    if not set_cols:
        raise ValueError("Nothing to update")

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("UPDATE {} SET {} WHERE {}").format(
                sql.Identifier(table),
                sql.SQL(", ").join(sql.SQL("{}=%s").format(sql.Identifier(c)) for c in set_cols),
                sql.SQL(" AND ").join(sql.SQL("{}=%s").format(sql.Identifier(c)) for c in pk_cols),
            ),
            [payload[c] for c in set_cols] + [pk_values[c] for c in pk_cols],
        )
        if cur.rowcount == 0:
            raise RuntimeError("Row not found or unchanged")
    conn.commit()


def delete_row(conn, table: str, pk_values: Dict) -> None:
    if table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    _, pk_cols = get_table_columns(conn, table)
    if not pk_cols:
        raise ValueError("Table has no primary key; cannot delete generically")

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("DELETE FROM {} WHERE {}").format(
                sql.Identifier(table),
                sql.SQL(" AND ").join(sql.SQL("{}=%s").format(sql.Identifier(c)) for c in pk_cols),
            ),
            [pk_values[c] for c in pk_cols],
        )
        if cur.rowcount == 0:
            raise RuntimeError("Row not found")
    conn.commit()
