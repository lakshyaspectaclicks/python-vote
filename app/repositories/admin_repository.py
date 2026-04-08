from __future__ import annotations

from app.utils.db import db


class AdminRepository:
    def get_by_username(self, username: str) -> dict | None:
        return db.fetch_one(
            """
            SELECT id, username, full_name, password_hash, is_active, created_at
            FROM admins
            WHERE username = %s
            """,
            (username,),
        )

    def get_by_id(self, admin_id: int) -> dict | None:
        return db.fetch_one(
            """
            SELECT id, username, full_name, is_active, created_at
            FROM admins
            WHERE id = %s
            """,
            (admin_id,),
        )

    def create(self, username: str, full_name: str, password_hash: str) -> int:
        return db.execute(
            """
            INSERT INTO admins (username, full_name, password_hash, is_active)
            VALUES (%s, %s, %s, 1)
            """,
            (username, full_name, password_hash),
        )

    def update_last_login(self, admin_id: int) -> None:
        db.execute(
            "UPDATE admins SET last_login_at = NOW() WHERE id = %s",
            (admin_id,),
        )

