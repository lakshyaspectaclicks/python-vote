from app.services.result_service import ResultService


def test_results_tally_and_tie(monkeypatch):
    service = ResultService()
    monkeypatch.setattr(service.election_repo, "get_by_id", lambda _id: {"id": 1, "name": "Prefects", "status": "CLOSED"})
    monkeypatch.setattr(
        service.result_repo,
        "get_position_candidate_tally",
        lambda _id: [
            {
                "position_id": 1,
                "position_name": "Head Boy",
                "display_order": 1,
                "candidate_id": 11,
                "candidate_name": "A",
                "candidate_class": "SS3",
                "vote_count": 15,
            },
            {
                "position_id": 1,
                "position_name": "Head Boy",
                "display_order": 1,
                "candidate_id": 12,
                "candidate_name": "B",
                "candidate_class": "SS3",
                "vote_count": 15,
            },
        ],
    )
    monkeypatch.setattr(service.voter_repo, "count_registered", lambda _id: 50)
    monkeypatch.setattr(service.ballot_repo, "count_ballots", lambda _id: 40)

    result = service.get_results(1, admin_preview=True)
    assert result["totals"]["turnout_percent"] == 80.0
    statuses = [c["status"] for c in result["positions"][0]["candidates"]]
    assert statuses == ["Tie", "Tie"]

