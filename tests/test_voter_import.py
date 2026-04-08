from io import BytesIO

from werkzeug.datastructures import FileStorage

from app.services.voter_service import VoterService


def test_voter_import_summary(monkeypatch):
    service = VoterService()
    monkeypatch.setattr(service.repo, "upsert_pin", lambda *args, **kwargs: None)
    monkeypatch.setattr(service.audit_repo, "log", lambda **kwargs: 1)

    csv_bytes = (
        b"student_id,full_name,class_name,pin\n"
        b"STU001,Ada One,SS1,\n"
        b"STU002,Ben Two,SS2,1234\n"
    )
    fs = FileStorage(stream=BytesIO(csv_bytes), filename="voters.csv", content_type="text/csv")

    # Replace generic exception with IntegrityError-like failure path
    from mysql.connector.errors import IntegrityError

    def fake_create_with_integrity(**kwargs):
        if kwargs["student_id"] == "STU002":
            raise IntegrityError(msg="duplicate")
        return 1

    monkeypatch.setattr(service.repo, "create", fake_create_with_integrity)
    summary = service.import_voters_from_csv(
        election_id=1,
        file_storage=fs,
        admin_id=1,
        ip="127.0.0.1",
        user_agent="pytest",
    )

    assert summary["imported"] == 1
    assert summary["failed"] == 1
    assert any("STU002" in err for err in summary["errors"])
