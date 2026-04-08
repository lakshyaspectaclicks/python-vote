from __future__ import annotations

from app.repositories.audit_repository import AuditLogRepository
from app.repositories.election_repository import ElectionRepository
from app.utils.exceptions import ElectionStateError, ValidationError


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"OPEN", "PAUSED", "CLOSED"},
    "OPEN": {"PAUSED", "CLOSED"},
    "PAUSED": {"OPEN", "CLOSED"},
    "CLOSED": set(),
}


class ElectionService:
    def __init__(self) -> None:
        self.repo = ElectionRepository()
        self.audit_repo = AuditLogRepository()

    def list_elections(self) -> list[dict]:
        return self.repo.list_all()

    def get_election(self, election_id: int) -> dict | None:
        return self.repo.get_by_id(election_id)

    def get_open_election(self) -> dict | None:
        return self.repo.get_open_election()

    def create_election(
        self,
        *,
        name: str,
        description: str | None,
        start_at: str | None,
        end_at: str | None,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> int:
        name = name.strip()
        if len(name) < 3:
            raise ValidationError("Election name must be at least 3 characters.")
        election_id = self.repo.create(
            name=name,
            description=description.strip() if description else None,
            start_at=start_at or None,
            end_at=end_at or None,
            created_by=admin_id,
        )
        self.audit_repo.log(
            admin_id=admin_id,
            action="ELECTION_CREATE",
            entity_type="ELECTION",
            entity_id=election_id,
            details=f"Created election '{name}'.",
            ip_address=ip,
            user_agent=user_agent,
        )
        return election_id

    def update_election(
        self,
        *,
        election_id: int,
        name: str,
        description: str | None,
        start_at: str | None,
        end_at: str | None,
        results_visible: bool,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        election = self.repo.get_by_id(election_id)
        if not election:
            raise ValidationError("Election not found.")
        if election["status"] == "CLOSED":
            raise ElectionStateError("Closed elections cannot be edited.")

        self.repo.update(
            election_id,
            name=name.strip(),
            description=description.strip() if description else None,
            start_at=start_at or None,
            end_at=end_at or None,
            results_visible=results_visible,
        )
        self.audit_repo.log(
            admin_id=admin_id,
            action="ELECTION_EDIT",
            entity_type="ELECTION",
            entity_id=election_id,
            details=f"Updated election '{name.strip()}'.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def delete_election(
        self,
        *,
        election_id: int,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        election = self.repo.get_by_id(election_id)
        if not election:
            raise ValidationError("Election not found.")
        if election["status"] != "DRAFT":
            raise ElectionStateError("Only draft elections can be deleted.")
        if self.repo.count_ballots(election_id) > 0:
            raise ElectionStateError("Election with ballots cannot be deleted.")
        self.repo.delete(election_id)
        self.audit_repo.log(
            admin_id=admin_id,
            action="ELECTION_DELETE",
            entity_type="ELECTION",
            entity_id=election_id,
            details=f"Deleted election '{election['name']}'.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def change_status(
        self,
        *,
        election_id: int,
        next_status: str,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        election = self.repo.get_by_id(election_id)
        if not election:
            raise ValidationError("Election not found.")

        current_status = election["status"]
        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if next_status not in allowed:
            raise ElectionStateError(
                f"Invalid status transition from {current_status} to {next_status}."
            )
        if next_status == "OPEN":
            if self.repo.count_positions(election_id) == 0:
                raise ElectionStateError("Cannot open election without positions.")
            if self.repo.count_candidates(election_id) == 0:
                raise ElectionStateError("Cannot open election without candidates.")
            if self.repo.count_voters(election_id) == 0:
                raise ElectionStateError("Cannot open election without active voters.")
            existing_open = self.repo.get_open_election()
            if existing_open and existing_open["id"] != election_id:
                raise ElectionStateError(
                    "Another election is already open. Pause/close it first."
                )

        self.repo.update_status(election_id, next_status)
        self.audit_repo.log(
            admin_id=admin_id,
            action=f"ELECTION_{next_status}",
            entity_type="ELECTION",
            entity_id=election_id,
            details=f"Election moved from {current_status} to {next_status}.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def dashboard_stats(self) -> dict:
        elections = self.repo.list_all()
        return {
            "total_elections": len(elections),
            "open_elections": sum(1 for e in elections if e["status"] == "OPEN"),
            "closed_elections": sum(1 for e in elections if e["status"] == "CLOSED"),
            "draft_elections": sum(1 for e in elections if e["status"] == "DRAFT"),
        }

