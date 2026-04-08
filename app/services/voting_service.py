from __future__ import annotations

from mysql.connector.errors import IntegrityError
from passlib.hash import bcrypt

from app.repositories.ballot_repository import BallotRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.voter_repository import VoterRepository
from app.utils.exceptions import DuplicateVoteError, ElectionStateError, ValidationError


class VotingService:
    def __init__(self) -> None:
        self.election_repo = ElectionRepository()
        self.position_repo = PositionRepository()
        self.candidate_repo = CandidateRepository()
        self.voter_repo = VoterRepository()
        self.ballot_repo = BallotRepository()

    def get_active_election(self) -> dict | None:
        return self.election_repo.get_open_election()

    def verify_voter(self, *, election_id: int, student_id: str, pin: str | None) -> dict:
        election = self.election_repo.get_by_id(election_id)
        if not election or election["status"] != "OPEN":
            raise ElectionStateError("Election is not currently open.")

        voter = self.voter_repo.get_by_student_id(election_id, student_id.strip().upper())
        if not voter or not voter["is_active"]:
            raise ValidationError("Voter not found or inactive.")

        if voter.get("pin_required"):
            if not pin:
                raise ValidationError("PIN is required for this voter.")
            if not voter.get("pin_hash") or not bcrypt.verify(pin, voter["pin_hash"]):
                raise ValidationError("Invalid PIN.")

        if self.ballot_repo.has_voted(election_id, voter["id"]):
            raise DuplicateVoteError("This student has already voted.")

        return voter

    def get_ballot_data(self, election_id: int) -> list[dict]:
        positions = self.position_repo.list_by_election(election_id)
        candidates = self.candidate_repo.list_for_ballot(election_id)
        by_position: dict[int, list[dict]] = {}
        for candidate in candidates:
            by_position.setdefault(candidate["position_id"], []).append(candidate)
        ballot = []
        for position in positions:
            options = by_position.get(position["id"], [])
            if options:
                ballot.append({**position, "candidates": options})
        return ballot

    def validate_selections(self, election_id: int, selections: dict[int, int]) -> list[tuple[int, int]]:
        ballot_data = self.get_ballot_data(election_id)
        if not ballot_data:
            raise ValidationError("No ballot positions with candidates are available.")

        validated: list[tuple[int, int]] = []
        for position in ballot_data:
            position_id = position["id"]
            candidate_ids = {c["id"] for c in position["candidates"]}
            selected_candidate = selections.get(position_id)
            if selected_candidate is None:
                raise ValidationError(f"Please select a candidate for {position['name']}.")
            if selected_candidate not in candidate_ids:
                raise ValidationError(f"Invalid candidate selected for {position['name']}.")
            validated.append((position_id, selected_candidate))
        return validated

    def submit_vote(
        self,
        *,
        election_id: int,
        voter_id: int,
        selections: dict[int, int],
        client_ip: str | None,
        user_agent: str | None,
    ) -> int:
        election = self.election_repo.get_by_id(election_id)
        if not election or election["status"] != "OPEN":
            raise ElectionStateError("Election is not currently open.")
        if self.ballot_repo.has_voted(election_id, voter_id):
            raise DuplicateVoteError("A ballot already exists for this voter.")

        validated = self.validate_selections(election_id, selections)
        try:
            return self.ballot_repo.create_ballot_with_items(
                election_id=election_id,
                voter_id=voter_id,
                selections=validated,
                client_ip=client_ip,
                user_agent=user_agent,
            )
        except IntegrityError as exc:
            raise DuplicateVoteError("Duplicate vote prevented by database constraints.") from exc

