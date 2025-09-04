# -*- coding: utf-8 -*-
"""
DB connection utilities for the Gym Management App.

- `connect()` is a context manager that opens a psycopg2 connection,
  yields it, rolls back on error, and always closes cleanly.

Environment variables (optional):
  DB_HOST (default: "localhost")
  DB_PORT (default: "5432")
  DB_NAME (default: "gym_db")
  DB_USER (default: "yehuda")
  DB_PASSWORD (default: "ninga")
"""

from __future__ import annotations

import os
from contextlib import contextmanager
import psycopg2


def _get_conn_params() -> dict:
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ.get("DB_NAME", "gym_db"),
        "user": os.environ.get("DB_USER", "yehuda"),
        "password": os.environ.get("DB_PASSWORD", "ninga"),
    }


@contextmanager
def connect():
    """
    Usage:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    params = _get_conn_params()
    conn = None
    try:
        conn = psycopg2.connect(**params)
        yield conn
    except Exception:
        try:
            if conn is not None:
                conn.rollback()
        finally:
            raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
