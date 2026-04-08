from __future__ import annotations

from app.utils.db import db


class ElectionRepository:
    def list_all(self) -> list[dict]:
        return db.fetch_all(
            """
            SELECT id, name, description, status, start_at, end_at, results_visible,
                   created_by, created_at, updated_at
            FROM elections
            ORDER BY created_at DESC
            """
        )

    def get_by_id(self, election_id: int) -> dict | None:
        return db.fetch_one(
            """
            SELECT id, name, description, status, start_at, end_at, results_visible,
                   created_by, created_at, updated_at
            FROM elections
            WHERE id = %s
            """,
            (election_id,),
        )

    def get_open_election(self) -> dict | None:
        return db.fetch_one(
            """
            SELECT id, name, description, status, start_at, end_at, results_visible
            FROM elections
            WHERE status = 'OPEN'
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """
        )

    def create(
        self,
        *,
        name: str,
        description: str | None,
        start_at: str | None,
        end_at: str | None,
        created_by: int,
    ) -> int:
        return db.execute(
            """
            INSERT INTO elections (name, description, start_at, end_at, status, created_by)
            VALUES (%s, %s, %s, %s, 'DRAFT', %s)
            """,
            (name, description, start_at, end_at, created_by),
        )

    def update(
        self,
        election_id: int,
        *,
        name: str,
        description: str | None,
        start_at: str | None,
        end_at: str | None,
        results_visible: bool,
    ) -> None:
        db.execute(
            """
            UPDATE elections
            SET name = %s, description = %s, start_at = %s, end_at = %s,
                results_visible = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (name, description, start_at, end_at, int(results_visible), election_id),
        )

    def update_status(self, election_id: int, status: str) -> None:
        db.execute(
            """
            UPDATE elections
            SET status = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (status, election_id),
        )

    def delete(self, election_id: int) -> None:
        db.execute("DELETE FROM elections WHERE id = %s", (election_id,))

    def count_positions(self, election_id: int) -> int:
        row = db.fetch_one(
            "SELECT COUNT(*) AS count FROM positions WHERE election_id = %s",
            (election_id,),
        )
        return int(row["count"]) if row else 0

    def count_candidates(self, election_id: int) -> int:
        row = db.fetch_one(
            "SELECT COUNT(*) AS count FROM candidates WHERE election_id = %s",
            (election_id,),
        )
        return int(row["count"]) if row else 0

    def count_voters(self, election_id: int) -> int:
        row = db.fetch_one(
            "SELECT COUNT(*) AS count FROM voters WHERE election_id = %s AND is_active = 1",
            (election_id,),
        )
        return int(row["count"]) if row else 0

    def count_ballots(self, election_id: int) -> int:
        row = db.fetch_one(
            "SELECT COUNT(*) AS count FROM ballots WHERE election_id = %s",
            (election_id,),
        )
        return int(row["count"]) if row else 0

