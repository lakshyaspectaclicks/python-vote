from __future__ import annotations

from passlib.hash import bcrypt

from app.repositories.admin_repository import AdminRepository
from app.repositories.audit_repository import AuditLogRepository
from app.utils.exceptions import AuthenticationError, ValidationError


class AuthService:
    def __init__(self) -> None:
        self.admin_repo = AdminRepository()
        self.audit_repo = AuditLogRepository()

    def login(self, *, username: str, password: str, ip: str | None, user_agent: str | None) -> dict:
        if not username or not password:
            raise ValidationError("Username and password are required.")

        admin = self.admin_repo.get_by_username(username)
        if not admin or not admin["is_active"]:
            raise AuthenticationError("Invalid credentials.")
        if not bcrypt.verify(password, admin["password_hash"]):
            raise AuthenticationError("Invalid credentials.")

        self.admin_repo.update_last_login(admin["id"])
        self.audit_repo.log(
            admin_id=admin["id"],
            action="ADMIN_LOGIN",
            entity_type="AUTH",
            entity_id=admin["id"],
            details=f"Admin {admin['username']} logged in.",
            ip_address=ip,
            user_agent=user_agent,
        )
        return admin

    def logout(self, *, admin_id: int, ip: str | None, user_agent: str | None) -> None:
        self.audit_repo.log(
            admin_id=admin_id,
            action="ADMIN_LOGOUT",
            entity_type="AUTH",
            entity_id=admin_id,
            details="Admin logged out.",
            ip_address=ip,
            user_agent=user_agent,
        )

    def create_admin(self, *, username: str, full_name: str, password: str) -> int:
        username = username.strip()
        full_name = full_name.strip()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        if self.admin_repo.get_by_username(username):
            raise ValidationError("Username already exists.")

        password_hash = bcrypt.hash(password)
        return self.admin_repo.create(username, full_name, password_hash)

