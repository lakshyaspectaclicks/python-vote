from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

import mysql.connector
from flask import Flask, current_app
from mysql.connector import pooling


class Database:
    def __init__(self) -> None:
        self._pool: pooling.MySQLConnectionPool | None = None

    def init_app(self, app: Flask) -> None:
        app.extensions["db"] = self

    def _ensure_pool(self) -> pooling.MySQLConnectionPool:
        if self._pool is None:
            self._pool = pooling.MySQLConnectionPool(
                pool_name=current_app.config["DB_POOL_NAME"],
                pool_size=current_app.config["DB_POOL_SIZE"],
                pool_reset_session=True,
                host=current_app.config["DB_HOST"],
                port=current_app.config["DB_PORT"],
                database=current_app.config["DB_NAME"],
                user=current_app.config["DB_USER"],
                password=current_app.config["DB_PASSWORD"],
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                use_pure=True,
            )
        return self._pool

    @contextmanager
    def connection(self) -> Generator[mysql.connector.MySQLConnection, None, None]:
        conn = self._ensure_pool().get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def cursor(
        self,
        *,
        dictionary: bool = True,
        connection: mysql.connector.MySQLConnection | None = None,
    ) -> Generator[tuple[mysql.connector.MySQLConnection, Any], None, None]:
        owns_connection = connection is None
        conn = connection
        if conn is None:
            conn = self._ensure_pool().get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield conn, cursor
        finally:
            cursor.close()
            if owns_connection:
                conn.close()

    @contextmanager
    def transaction(self) -> Generator[mysql.connector.MySQLConnection, None, None]:
        with self.connection() as conn:
            try:
                conn.start_transaction()
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.cursor(dictionary=True) as (_, cur):
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.cursor(dictionary=True) as (_, cur):
            cur.execute(query, params)
            return cur.fetchall()

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> int:
        with self.connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(query, params)
                conn.commit()
                return cur.lastrowid
            finally:
                cur.close()


db = Database()
