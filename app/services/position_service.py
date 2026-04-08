from __future__ import annotations

from app.repositories.audit_repository import AuditLogRepository
from app.repositories.position_repository import PositionRepository
from app.utils.exceptions import ValidationError


class PositionService:
    def __init__(self) -> None:
        self.repo = PositionRepository()
        self.audit_repo = AuditLogRepository()

    def list_positions(self, election_id: int) -> list[dict]:
        return self.repo.list_by_election(election_id)

    def get_position(self, position_id: int) -> dict | None:
        return self.repo.get_by_id(position_id)

    def create_position(
        self,
        *,
        election_id: int,
        name: str,
        display_order: int,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> int:
        name = name.strip()
        if not name:
            raise ValidationError("Position name is required.")
        position_id = self.repo.create(election_id, name, display_order)
        self.audit_repo.log(
            admin_id=admin_id,
            action="POSITION_CREATE",
            entity_type="POSITION",
            entity_id=position_id,
            details=f"Created position '{name}' for election {election_id}.",
            ip_address=ip,
            user_agent=user_agent,
        )
        return position_id

    def update_position(
        self,
        *,
        position_id: int,
        name: str,
        display_order: int,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        position = self.repo.get_by_id(position_id)
        if not position:
            raise ValidationError("Position not found.")
        self.repo.update(position_id, name.strip(), display_order)
        self.audit_repo.log(
            admin_id=admin_id,
            action="POSITION_EDIT",
            entity_type="POSITION",
            entity_id=position_id,
            details=f"Updated position '{name.strip()}'.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def delete_position(
        self,
        *,
        position_id: int,
        admin_id: int,
        ip: str | None,
        user_agent: str | None,
    ) -> None:
        position = self.repo.get_by_id(position_id)
        if not position:
            raise ValidationError("Position not found.")
        self.repo.delete(position_id)
        self.audit_repo.log(
            admin_id=admin_id,
            action="POSITION_DELETE",
            entity_type="POSITION",
            entity_id=position_id,
            details=f"Deleted position '{position['name']}'.",
            ip_address=ip,
            user_agent=user_agent,
        )

