from __future__ import annotations

from collections import defaultdict

from flask import current_app

from app.repositories.ballot_repository import BallotRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.result_repository import ResultRepository
from app.repositories.voter_repository import VoterRepository
from app.utils.exceptions import ElectionStateError, ValidationError


class ResultService:
    def __init__(self) -> None:
        self.election_repo = ElectionRepository()
        self.result_repo = ResultRepository()
        self.voter_repo = VoterRepository()
        self.ballot_repo = BallotRepository()

    def get_results(self, election_id: int, *, admin_preview: bool = False) -> dict:
        election = self.election_repo.get_by_id(election_id)
        if not election:
            raise ValidationError("Election not found.")

        if election["status"] != "CLOSED":
            preview_enabled = current_app.config.get("RESULTS_PREVIEW_BEFORE_CLOSE", False)
            if not admin_preview and not preview_enabled:
                raise ElectionStateError("Results are available only after election closure.")

        rows = self.result_repo.get_position_candidate_tally(election_id)
        grouped: dict[int, dict] = {}
        for row in rows:
            position = grouped.setdefault(
                row["position_id"],
                {
                    "position_id": row["position_id"],
                    "position_name": row["position_name"],
                    "display_order": row["display_order"],
                    "candidates": [],
                },
            )
            position["candidates"].append(
                {
                    "candidate_id": row["candidate_id"],
                    "candidate_name": row["candidate_name"],
                    "candidate_class": row["candidate_class"],
                    "vote_count": int(row["vote_count"]),
                    "status": "",
                }
            )

        positions = sorted(grouped.values(), key=lambda item: item["display_order"])
        for position in positions:
            top = defaultdict(list)
            max_votes = 0
            for candidate in position["candidates"]:
                votes = candidate["vote_count"]
                top[votes].append(candidate)
                max_votes = max(max_votes, votes)
            top_candidates = top[max_votes]
            if max_votes == 0:
                for candidate in position["candidates"]:
                    candidate["status"] = "No votes"
            elif len(top_candidates) > 1:
                for candidate in top_candidates:
                    candidate["status"] = "Tie"
            else:
                top_candidates[0]["status"] = "Winner"

        registered = self.voter_repo.count_registered(election_id)
        cast = self.ballot_repo.count_ballots(election_id)
        turnout = round((cast / registered) * 100, 2) if registered else 0.0
        return {
            "election": election,
            "positions": positions,
            "totals": {
                "registered_voters": registered,
                "ballots_cast": cast,
                "turnout_percent": turnout,
            },
        }

