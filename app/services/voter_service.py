from __future__ import annotations

import csv
import io

from mysql.connector.errors import IntegrityError
from passlib.hash import bcrypt

from app.repositories.audit_repository import AuditLogRepository
from app.repositories.ballot_repository import BallotRepository
from app.repositories.voter_repository import VoterRepository
from app.utils.exceptions import ValidationError


class VoterService:
    def __init__(self) -> None:
        self.repo = VoterRepository()
        self.ballot_repo = BallotRepository()
        self.audit_repo = AuditLogRepository()

    def list_voters(self, election_id: int) -> list[dict]:
        return self.repo.list_by_election(election_id)

    def get_voter(self, voter_id: int) -> dict | None:
        return self.repo.get_by_id(voter_id)

    def create_voter(
        self,
        *,
        election_id: int,
        student_id: str,
        full_name: str,
        class_name: str,
        pin: str | None,
        pin_required: bool,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> int:
        student_id = student_id.strip().upper()
        if not student_id:
            raise ValidationError("Student ID is required.")
        if not full_name.strip():
            raise ValidationError("Voter name is required.")
        if self.repo.get_by_student_id(election_id, student_id):
            raise ValidationError("Student ID already exists for this election.")
        if pin_required and not (pin and pin.strip()):
            raise ValidationError("PIN is required when PIN-required is enabled.")

        voter_id = self.repo.create(
            election_id=election_id,
            student_id=student_id,
            full_name=full_name.strip(),
            class_name=class_name.strip(),
            is_active=True,
        )
        pin_hash = bcrypt.hash(pin.strip()) if pin and pin.strip() else None
        self.repo.upsert_pin(voter_id, pin_hash, pin_required)
        self.audit_repo.log(
            admin_id=admin_id,
            action="VOTER_CREATE",
            entity_type="VOTER",
            entity_id=voter_id,
            details=f"Created voter {student_id}.",
            ip_address=ip,
            user_agent=user_agent,
        )
        return voter_id

    def update_voter(
        self,
        *,
        voter_id: int,
        student_id: str,
        full_name: str,
        class_name: str,
        pin: str | None,
        pin_required: bool,
        is_active: bool,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        voter = self.repo.get_by_id(voter_id)
        if not voter:
            raise ValidationError("Voter not found.")
        student_id = student_id.strip().upper()
        duplicate = self.repo.get_by_student_id(voter["election_id"], student_id)
        if duplicate and duplicate["id"] != voter_id:
            raise ValidationError("Student ID already exists for this election.")

        self.repo.update(
            voter_id,
            student_id=student_id,
            full_name=full_name.strip(),
            class_name=class_name.strip(),
            is_active=is_active,
        )

        existing_pin_hash = voter.get("pin_hash")
        if pin is not None and pin.strip():
            existing_pin_hash = bcrypt.hash(pin.strip())
        if pin_required and not existing_pin_hash:
            raise ValidationError("PIN is required when PIN-required is enabled.")
        self.repo.upsert_pin(voter_id, existing_pin_hash, pin_required)
        self.audit_repo.log(
            admin_id=admin_id,
            action="VOTER_EDIT",
            entity_type="VOTER",
            entity_id=voter_id,
            details=f"Updated voter {student_id}.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def delete_voter(
        self,
        *,
        voter_id: int,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        voter = self.repo.get_by_id(voter_id)
        if not voter:
            raise ValidationError("Voter not found.")
        if self.ballot_repo.has_voted(voter["election_id"], voter_id):
            raise ValidationError("Cannot delete voter after a submitted ballot.")
        self.repo.delete(voter_id)
        self.audit_repo.log(
            admin_id=admin_id,
            action="VOTER_DELETE",
            entity_type="VOTER",
            entity_id=voter_id,
            details=f"Deleted voter {voter['student_id']}.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def import_voters_from_csv(
        self,
        *,
        election_id: int,
        file_storage,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> dict:
        if not file_storage or not file_storage.filename:
            raise ValidationError("CSV file is required.")

        content = file_storage.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        expected = {"student_id", "full_name", "class_name", "pin"}
        if not reader.fieldnames:
            raise ValidationError("CSV file is empty.")
        missing = expected - set(h.strip() for h in reader.fieldnames)
        if missing:
            raise ValidationError(f"CSV missing columns: {', '.join(sorted(missing))}.")

        imported = 0
        failed = 0
        errors: list[str] = []
        seen_ids: set[str] = set()
        line = 1
        for row in reader:
            line += 1
            student_id = (row.get("student_id") or "").strip().upper()
            full_name = (row.get("full_name") or "").strip()
            class_name = (row.get("class_name") or "").strip()
            pin = (row.get("pin") or "").strip()

            if not student_id or not full_name or not class_name:
                failed += 1
                errors.append(f"Line {line}: required fields missing.")
                continue
            if student_id in seen_ids:
                failed += 1
                errors.append(f"Line {line}: duplicate student_id '{student_id}' in file.")
                continue
            seen_ids.add(student_id)

            try:
                voter_id = self.repo.create(
                    election_id=election_id,
                    student_id=student_id,
                    full_name=full_name,
                    class_name=class_name,
                    is_active=True,
                )
                pin_hash = bcrypt.hash(pin) if pin else None
                self.repo.upsert_pin(voter_id, pin_hash, bool(pin))
                imported += 1
            except IntegrityError:
                failed += 1
                errors.append(f"Line {line}: student_id '{student_id}' already exists.")

        self.audit_repo.log(
            admin_id=admin_id,
            action="VOTER_IMPORT",
            entity_type="VOTER",
            entity_id=election_id,
            details=f"Imported={imported}, Failed={failed}",
            ip_address=ip,
            user_agent=user_agent,
        )
        return {"imported": imported, "failed": failed, "errors": errors}
