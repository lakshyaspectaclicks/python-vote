from __future__ import annotations

from typing import Iterable

from mysql.connector.errors import IntegrityError

from app.utils.db import db


class BallotRepository:
    def has_voted(self, election_id: int, voter_id: int) -> bool:
        row = db.fetch_one(
            """
            SELECT id
            FROM ballots
            WHERE election_id = %s AND voter_id = %s
            LIMIT 1
            """,
            (election_id, voter_id),
        )
        return row is not None

    def create_ballot_with_items(
        self,
        *,
        election_id: int,
        voter_id: int,
        selections: Iterable[tuple[int, int]],
        client_ip: str | None,
        user_agent: str | None,
    ) -> int:
        with db.transaction() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO ballots (election_id, voter_id, client_ip, user_agent)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (election_id, voter_id, client_ip, user_agent),
                )
                ballot_id = cur.lastrowid
                for position_id, candidate_id in selections:
                    cur.execute(
                        """
                        INSERT INTO ballot_items (ballot_id, position_id, candidate_id)
                        VALUES (%s, %s, %s)
                        """,
                        (ballot_id, position_id, candidate_id),
                    )
            except IntegrityError:
                raise
            finally:
                cur.close()
        return ballot_id

    def count_ballots(self, election_id: int) -> int:
        row = db.fetch_one(
            "SELECT COUNT(*) AS count FROM ballots WHERE election_id = %s",
            (election_id,),
        )
        return int(row["count"]) if row else 0

