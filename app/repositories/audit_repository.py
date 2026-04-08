from __future__ import annotations

from app.utils.db import db


class AuditLogRepository:
    def log(
        self,
        *,
        action: str,
        entity_type: str,
        admin_id: int | None = None,
        entity_id: int | None = None,
        details: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        return db.execute(
            """
            INSERT INTO audit_logs
            (admin_id, action, entity_type, entity_id, details, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (admin_id, action, entity_type, entity_id, details, ip_address, user_agent),
        )

    def list_logs(
        self,
        *,
        action: str | None = None,
        admin_id: int | None = None,
        limit: int = 200,
    ) -> list[dict]:
        query = """
            SELECT l.id, l.admin_id, l.action, l.entity_type, l.entity_id,
                   l.details, l.ip_address, l.user_agent, l.created_at,
                   a.username AS admin_username
            FROM audit_logs l
            LEFT JOIN admins a ON a.id = l.admin_id
            WHERE 1 = 1
        """
        params: list = []
        if action:
            query += " AND l.action = %s"
            params.append(action)
        if admin_id:
            query += " AND l.admin_id = %s"
            params.append(admin_id)
        query += " ORDER BY l.created_at DESC LIMIT %s"
        params.append(limit)
        return db.fetch_all(query, tuple(params))

