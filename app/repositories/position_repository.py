from __future__ import annotations

from app.utils.db import db


class PositionRepository:
    def list_by_election(self, election_id: int) -> list[dict]:
        return db.fetch_all(
            """
            SELECT id, election_id, name, display_order, created_at, updated_at
            FROM positions
            WHERE election_id = %s
            ORDER BY display_order ASC, id ASC
            """,
            (election_id,),
        )

    def get_by_id(self, position_id: int) -> dict | None:
        return db.fetch_one(
            """
            SELECT id, election_id, name, display_order, created_at, updated_at
            FROM positions
            WHERE id = %s
            """,
            (position_id,),
        )

    def create(self, election_id: int, name: str, display_order: int) -> int:
        return db.execute(
            """
            INSERT INTO positions (election_id, name, display_order)
            VALUES (%s, %s, %s)
            """,
            (election_id, name, display_order),
        )

    def update(self, position_id: int, name: str, display_order: int) -> None:
        db.execute(
            """
            UPDATE positions
            SET name = %s, display_order = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (name, display_order, position_id),
        )

    def delete(self, position_id: int) -> None:
        db.execute("DELETE FROM positions WHERE id = %s", (position_id,))

