def _payload():
    return {
        "election": {"id": 1, "name": "Prefects", "status": "CLOSED"},
        "positions": [
            {
                "position_name": "Head Boy",
                "candidates": [
                    {
                        "candidate_name": "A",
                        "candidate_class": "SS3",
                        "vote_count": 10,
                        "status": "Winner",
                    }
                ],
            }
        ],
        "totals": {"registered_voters": 100, "ballots_cast": 80, "turnout_percent": 80.0},
    }


def test_csv_export_endpoint(monkeypatch, logged_in_client):
    from app.routes import exports as export_routes

    monkeypatch.setattr(export_routes.result_service, "get_results", lambda election_id, admin_preview: _payload())
    monkeypatch.setattr(export_routes.export_service, "build_results_csv", lambda payload: b"a,b,c\n")
    monkeypatch.setattr(export_routes.audit_repo, "log", lambda **kwargs: 1)

    response = logged_in_client.get("/admin/elections/1/export/csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"a,b,c" in response.data


def test_pdf_export_endpoint(monkeypatch, logged_in_client):
    from app.routes import exports as export_routes

    monkeypatch.setattr(export_routes.result_service, "get_results", lambda election_id, admin_preview: _payload())
    monkeypatch.setattr(export_routes.export_service, "build_results_pdf", lambda payload: b"%PDF-1.4 test")
    monkeypatch.setattr(export_routes.audit_repo, "log", lambda **kwargs: 1)

    response = logged_in_client.get("/admin/elections/1/export/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")

