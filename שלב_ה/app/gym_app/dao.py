# -*- coding: utf-8 -*-
"""
DAO layer for Gym Management App (Tkinter + PostgreSQL).
All DB-facing functions live here. Each write operation commits.
"""

from __future__ import annotations

from typing import Optional, Tuple, List, Dict
from datetime import date, datetime
from psycopg2 import sql


# =========================
#  Authentication & Users
# =========================

def authenticate_user(conn, username: str, password: str) -> Optional[Tuple[int, int, str]]:
    """
    Calls DB function authenticate_user(username, password) → (user_id, personid, role)
    Returns None if credentials are invalid.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM authenticate_user(%s, %s)", (username, password))
        row = cur.fetchone()
    return row if row else None


def change_password_by_pid(conn, pid: int, current_password: str, new_password: str) -> bool:
    """
    Calls DB function change_password_by_pid(pid, current_password, new_password) → boolean.
    Returns True on success.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT change_password_by_pid(%s, %s, %s)",
            (pid, current_password, new_password),
        )
        ok = bool(cur.fetchone()[0])
    conn.commit()
    return ok


def admin_reset_password_by_pid(conn, pid: int) -> None:
    """
    Calls DB function admin_reset_password_by_pid(pid).
    Expected behavior: reset username/password to PID; create auth_user if missing.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT admin_reset_password_by_pid(%s)", (pid,))
    conn.commit()


def ensure_default_admin(conn) -> None:
    """
    Calls ensure_default_admin() to create PID=1 admin (user=1, pass=1) only if no admins exist.
    Safe to call at app startup.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT ensure_default_admin()")
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
    """
    Returns (rows, total) for shifts with optional filters.
    Rows are (pid, date, clock_in, clock_out).
    """
    # Build filters with simple parameter binding
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
    """
    Insert a new shift row.
    """
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
    """
    Update a shift identified by (pid, date, old_clock_in).
    """
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE shift SET clock_in=%s, clock_out=%s WHERE pid=%s AND "date"=%s AND clock_in=%s',
            (new_clock_in, clock_out, pid, sdate, old_clock_in),
        )
        if cur.rowcount == 0:
            raise RuntimeError("Shift not found or unchanged")
    conn.commit()


def delete_shift(conn, pid: int, sdate: date, clock_in: datetime) -> None:
    """
    Delete a shift identified by (pid, date, clock_in).
    """
    with conn.cursor() as cur:
        cur.execute(
            'DELETE FROM shift WHERE pid=%s AND "date"=%s AND clock_in=%s',
            (pid, sdate, clock_in),
        )
        if cur.rowcount == 0:
            raise RuntimeError("Shift not found")
    conn.commit()


# ===========================================
#  Generic Admin Data Manager (whitelisted)
# ===========================================

# Restrict which tables can be edited via the generic UI
ALLOWED_TABLES = [
    "person", "member", "worker", "hourly", "monthly", "freelance",
    "maintenanceworker", "gym", "accessdevice", "entryexit", "shift", "serves"
]


def list_allowed_tables() -> List[str]:
    """Return the allowed tables for the generic Data Manager."""
    return ALLOWED_TABLES[:]


def get_table_columns(conn, table: str) -> Tuple[List[Dict], List[str]]:
    """
    Introspect columns and primary key columns for a given table.
    Returns: (columns, pk_cols)
      columns: [{name, data_type, nullable, default}]
      pk_cols: [col, ...] ordered
    """
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
    """
    Fetch rows for a given table with optional search (ILIKE for text) and sort.
    Returns: (rows, total, col_names, cols_meta, pk_cols)
    """
    if table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    cols_meta, pk_cols = get_table_columns(conn, table)
    col_names = [c["name"] for c in cols_meta]

    # WHERE
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

    # ORDER BY
    if sort_by and sort_by in col_names:
        direction = "DESC" if str(sort_dir).upper().startswith("D") else "ASC"
        order_sql = sql.SQL("ORDER BY {} {} NULLS LAST").format(
            sql.Identifier(sort_by), sql.SQL(direction)
        )
    else:
        # default: by PK; else first column
        order_cols = pk_cols if pk_cols else col_names[:1]
        order_sql = sql.SQL("ORDER BY {} NULLS LAST").format(
            sql.SQL(", ").join(sql.Identifier(c) for c in order_cols)
        )

    with conn.cursor() as cur:
        # total
        cur.execute(
            sql.SQL("SELECT COUNT(*) FROM {} {}").format(
                sql.Identifier(table), where_sql
            ),
            where_args,
        )
        total = int(cur.fetchone()[0])

        # page
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


def insert_row(conn, table: str, payload: Dict) -> None:
    """
    Insert a row. payload maps column->value (strings are fine; PG will cast when possible).
    Skips columns not in table.
    """
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
    """
    Update a row by primary key. payload is non-PK fields.
    """
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
    """
    Delete a row by primary key (composite keys supported).
    """
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


# ===========================================
#  Person helpers (dependency resolution)
# ===========================================

def person_exists(conn, pid: int) -> bool:
    """Return True if person(pid) exists."""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM person WHERE pid=%s", (pid,))
        return cur.fetchone() is not None


def insert_person(
    conn,
    pid: int,
    firstname: str,
    lastname: str,
    dateofb: str,  # 'YYYY-MM-DD'
    email: Optional[str] = None,
    address: Optional[str] = None,
    phone: Optional[str] = None,
) -> None:
    """
    Create a person row with all mandatory fields.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO person(pid, dateofb, firstname, lastname, email, address, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (pid, dateofb, firstname, lastname, email, address, phone),
        )
    conn.commit()
