from __future__ import annotations

from app.utils.db import db


class SettingsRepository:
    def get(self, key: str) -> str | None:
        row = db.fetch_one("SELECT setting_value FROM app_settings WHERE setting_key = %s", (key,))
        return row["setting_value"] if row else None

    def set(self, key: str, value: str) -> None:
        db.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), updated_at = NOW()
            """,
            (key, value),
        )

