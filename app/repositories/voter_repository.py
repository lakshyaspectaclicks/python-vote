from __future__ import annotations

from app.utils.db import db


class VoterRepository:
    def list_by_election(self, election_id: int) -> list[dict]:
        return db.fetch_all(
            """
            SELECT v.id, v.election_id, v.student_id, v.full_name, v.class_name, v.is_active,
                   vc.pin_required,
                   v.created_at, v.updated_at
            FROM voters v
            LEFT JOIN voter_credentials vc ON vc.voter_id = v.id
            WHERE v.election_id = %s
            ORDER BY v.full_name ASC
            """,
            (election_id,),
        )

    def get_by_id(self, voter_id: int) -> dict | None:
        return db.fetch_one(
            """
            SELECT v.id, v.election_id, v.student_id, v.full_name, v.class_name, v.is_active,
                   vc.pin_hash, vc.pin_required
            FROM voters v
            LEFT JOIN voter_credentials vc ON vc.voter_id = v.id
            WHERE v.id = %s
            """,
            (voter_id,),
        )

    def get_by_student_id(self, election_id: int, student_id: str) -> dict | None:
        return db.fetch_one(
            """
            SELECT v.id, v.election_id, v.student_id, v.full_name, v.class_name, v.is_active,
                   vc.pin_hash, vc.pin_required
            FROM voters v
            LEFT JOIN voter_credentials vc ON vc.voter_id = v.id
            WHERE v.election_id = %s AND v.student_id = %s
            """,
            (election_id, student_id),
        )

    def create(
        self,
        *,
        election_id: int,
        student_id: str,
        full_name: str,
        class_name: str,
        is_active: bool = True,
    ) -> int:
        return db.execute(
            """
            INSERT INTO voters (election_id, student_id, full_name, class_name, is_active)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (election_id, student_id, full_name, class_name, int(is_active)),
        )

    def update(
        self,
        voter_id: int,
        *,
        student_id: str,
        full_name: str,
        class_name: str,
        is_active: bool,
    ) -> None:
        db.execute(
            """
            UPDATE voters
            SET student_id = %s, full_name = %s, class_name = %s, is_active = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (student_id, full_name, class_name, int(is_active), voter_id),
        )

    def delete(self, voter_id: int) -> None:
        db.execute("DELETE FROM voters WHERE id = %s", (voter_id,))

    def upsert_pin(self, voter_id: int, pin_hash: str | None, pin_required: bool) -> None:
        db.execute(
            """
            INSERT INTO voter_credentials (voter_id, pin_hash, pin_required)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE pin_hash = VALUES(pin_hash), pin_required = VALUES(pin_required)
            """,
            (voter_id, pin_hash, int(pin_required)),
        )

    def count_registered(self, election_id: int) -> int:
        row = db.fetch_one(
            "SELECT COUNT(*) AS count FROM voters WHERE election_id = %s AND is_active = 1",
            (election_id,),
        )
        return int(row["count"]) if row else 0

