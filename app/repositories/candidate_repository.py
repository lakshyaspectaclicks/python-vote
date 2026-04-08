from __future__ import annotations

from app.utils.db import db


class CandidateRepository:
    def list_by_election(self, election_id: int) -> list[dict]:
        return db.fetch_all(
            """
            SELECT c.id, c.election_id, c.position_id, c.full_name, c.class_name, c.gender, c.bio,
                   c.photo_path, c.is_active, c.created_at, c.updated_at, p.name AS position_name
            FROM candidates c
            INNER JOIN positions p ON p.id = c.position_id
            WHERE c.election_id = %s
            ORDER BY p.display_order ASC, c.full_name ASC
            """,
            (election_id,),
        )

    def list_for_ballot(self, election_id: int) -> list[dict]:
        return db.fetch_all(
            """
            SELECT c.id, c.position_id, c.full_name, c.class_name, c.gender, c.bio, c.photo_path
            FROM candidates c
            WHERE c.election_id = %s AND c.is_active = 1
            ORDER BY c.full_name ASC
            """,
            (election_id,),
        )

    def get_by_id(self, candidate_id: int) -> dict | None:
        return db.fetch_one(
            """
            SELECT id, election_id, position_id, full_name, class_name, gender, bio, photo_path, is_active
            FROM candidates
            WHERE id = %s
            """,
            (candidate_id,),
        )

    def create(
        self,
        *,
        election_id: int,
        position_id: int,
        full_name: str,
        class_name: str,
        gender: str | None,
        bio: str | None,
        photo_path: str | None,
    ) -> int:
        return db.execute(
            """
            INSERT INTO candidates
            (election_id, position_id, full_name, class_name, gender, bio, photo_path, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (election_id, position_id, full_name, class_name, gender, bio, photo_path),
        )

    def update(
        self,
        candidate_id: int,
        *,
        position_id: int,
        full_name: str,
        class_name: str,
        gender: str | None,
        bio: str | None,
        photo_path: str | None,
        is_active: bool,
    ) -> None:
        db.execute(
            """
            UPDATE candidates
            SET position_id = %s, full_name = %s, class_name = %s, gender = %s,
                bio = %s, photo_path = %s, is_active = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (
                position_id,
                full_name,
                class_name,
                gender,
                bio,
                photo_path,
                int(is_active),
                candidate_id,
            ),
        )

    def delete(self, candidate_id: int) -> None:
        db.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))

