import pytest

from app.services.voting_service import VotingService
from app.utils.exceptions import DuplicateVoteError, ElectionStateError


def test_duplicate_vote_prevention(monkeypatch):
    service = VotingService()
    monkeypatch.setattr(service.election_repo, "get_by_id", lambda _id: {"id": 1, "status": "OPEN"})
    monkeypatch.setattr(service.ballot_repo, "has_voted", lambda election_id, voter_id: True)

    with pytest.raises(DuplicateVoteError):
        service.submit_vote(
            election_id=1,
            voter_id=10,
            selections={1: 20},
            client_ip="127.0.0.1",
            user_agent="pytest",
        )


def test_successful_vote_submission(monkeypatch):
    service = VotingService()
    monkeypatch.setattr(service.election_repo, "get_by_id", lambda _id: {"id": 1, "status": "OPEN"})
    monkeypatch.setattr(service.ballot_repo, "has_voted", lambda election_id, voter_id: False)
    monkeypatch.setattr(service, "validate_selections", lambda election_id, selections: [(1, 101), (2, 202)])
    monkeypatch.setattr(service.ballot_repo, "create_ballot_with_items", lambda **kwargs: 55)

    ballot_id = service.submit_vote(
        election_id=1,
        voter_id=10,
        selections={1: 101, 2: 202},
        client_ip="127.0.0.1",
        user_agent="pytest",
    )
    assert ballot_id == 55


def test_election_state_restriction(monkeypatch):
    service = VotingService()
    monkeypatch.setattr(service.election_repo, "get_by_id", lambda _id: {"id": 1, "status": "PAUSED"})
    monkeypatch.setattr(service.ballot_repo, "has_voted", lambda election_id, voter_id: False)

    with pytest.raises(ElectionStateError):
        service.submit_vote(
            election_id=1,
            voter_id=10,
            selections={1: 100},
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

