
# -*- coding: utf-8 -*-
"""
db.py - ניהול חיבורים (Connection Pool) + קונטקסט מנג'ר
"""
from contextlib import contextmanager
from psycopg2 import pool
from .config import DBConfig
import psycopg2
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, cfg: DBConfig):
        self.cfg = cfg
        self._pool = pool.SimpleConnectionPool(
            minconn=cfg.minconn,
            maxconn=cfg.maxconn,
            host=cfg.host,
            port=cfg.port,
            database=cfg.dbname,
            user=cfg.user,
            password=cfg.password,
        )
        logger.info("Connection pool created: %s", self._pool)

    @contextmanager
    def connect(self):
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.exception("DB error, rollback: %s", e)
            raise
        finally:
            self._pool.putconn(conn)

    def close_all(self):
        self._pool.closeall()
