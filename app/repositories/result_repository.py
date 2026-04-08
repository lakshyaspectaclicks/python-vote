from __future__ import annotations

from app.utils.db import db


class ResultRepository:
    def get_position_candidate_tally(self, election_id: int) -> list[dict]:
        return db.fetch_all(
            """
            SELECT
                p.id AS position_id,
                p.name AS position_name,
                p.display_order,
                c.id AS candidate_id,
                c.full_name AS candidate_name,
                c.class_name AS candidate_class,
                COUNT(bi.id) AS vote_count
            FROM positions p
            INNER JOIN candidates c ON c.position_id = p.id AND c.is_active = 1
            LEFT JOIN ballot_items bi ON bi.candidate_id = c.id
            LEFT JOIN ballots b ON b.id = bi.ballot_id AND b.election_id = p.election_id
            WHERE p.election_id = %s
            GROUP BY
                p.id, p.name, p.display_order,
                c.id, c.full_name, c.class_name
            ORDER BY p.display_order ASC, c.full_name ASC
            """,
            (election_id,),
        )

