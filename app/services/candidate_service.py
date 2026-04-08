from __future__ import annotations

from app.repositories.audit_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.position_repository import PositionRepository
from app.utils.exceptions import ValidationError
from app.utils.upload import delete_uploaded_file, save_candidate_photo


class CandidateService:
    def __init__(self) -> None:
        self.repo = CandidateRepository()
        self.position_repo = PositionRepository()
        self.audit_repo = AuditLogRepository()

    def list_candidates(self, election_id: int) -> list[dict]:
        return self.repo.list_by_election(election_id)

    def get_candidate(self, candidate_id: int) -> dict | None:
        return self.repo.get_by_id(candidate_id)

    def create_candidate(
        self,
        *,
        election_id: int,
        position_id: int,
        full_name: str,
        class_name: str,
        gender: str | None,
        bio: str | None,
        photo_file,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> int:
        position = self.position_repo.get_by_id(position_id)
        if not position or position["election_id"] != election_id:
            raise ValidationError("Invalid position selected.")
        if not full_name.strip():
            raise ValidationError("Candidate full name is required.")
        if not class_name.strip():
            raise ValidationError("Candidate class is required.")

        photo_path = save_candidate_photo(photo_file) if photo_file and photo_file.filename else None
        candidate_id = self.repo.create(
            election_id=election_id,
            position_id=position_id,
            full_name=full_name.strip(),
            class_name=class_name.strip(),
            gender=gender.strip() if gender else None,
            bio=bio.strip() if bio else None,
            photo_path=photo_path,
        )
        self.audit_repo.log(
            admin_id=admin_id,
            action="CANDIDATE_CREATE",
            entity_type="CANDIDATE",
            entity_id=candidate_id,
            details=f"Created candidate '{full_name.strip()}'.",
            ip_address=ip,
            user_agent=user_agent,
        )
        return candidate_id

    def update_candidate(
        self,
        *,
        candidate_id: int,
        position_id: int,
        full_name: str,
        class_name: str,
        gender: str | None,
        bio: str | None,
        photo_file,
        remove_photo: bool,
        is_active: bool,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        candidate = self.repo.get_by_id(candidate_id)
        if not candidate:
            raise ValidationError("Candidate not found.")
        position = self.position_repo.get_by_id(position_id)
        if not position or position["election_id"] != candidate["election_id"]:
            raise ValidationError("Invalid position selected.")

        photo_path = candidate["photo_path"]
        if remove_photo:
            delete_uploaded_file(photo_path)
            photo_path = None
        if photo_file and photo_file.filename:
            new_photo = save_candidate_photo(photo_file)
            delete_uploaded_file(photo_path)
            photo_path = new_photo

        self.repo.update(
            candidate_id,
            position_id=position_id,
            full_name=full_name.strip(),
            class_name=class_name.strip(),
            gender=gender.strip() if gender else None,
            bio=bio.strip() if bio else None,
            photo_path=photo_path,
            is_active=is_active,
        )
        self.audit_repo.log(
            admin_id=admin_id,
            action="CANDIDATE_EDIT",
            entity_type="CANDIDATE",
            entity_id=candidate_id,
            details=f"Updated candidate '{full_name.strip()}'.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def delete_candidate(
        self,
        *,
        candidate_id: int,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        candidate = self.repo.get_by_id(candidate_id)
        if not candidate:
            raise ValidationError("Candidate not found.")
        self.repo.delete(candidate_id)
        delete_uploaded_file(candidate.get("photo_path"))
        self.audit_repo.log(
            admin_id=admin_id,
            action="CANDIDATE_DELETE",
            entity_type="CANDIDATE",
            entity_id=candidate_id,
            details=f"Deleted candidate '{candidate['full_name']}'.",
            ip_address=ip,
            user_agent=user_agent,
        )

