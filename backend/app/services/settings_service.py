from sqlalchemy.orm import Session
from app.models import Setting
from app.core.security import hash_password, verify_password
from fastapi import HTTPException, status


class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_settings(self) -> dict[str, str]:
        settings = self.db.query(Setting).all()
        result = {s.key: s.value for s in settings}
        # Mask sensitive values
        if "ldap_admin_password" in result:
            result["ldap_admin_password"] = "********" if result["ldap_admin_password"] else ""
        if "admin_password_hash" in result:
            result["admin_password_hash"] = "********"
        return result

    def get_public_settings(self) -> dict[str, str]:
        """Return non-sensitive settings for frontend use."""
        settings = self.db.query(Setting).filter(
            Setting.key.in_(["ldap_server_url", "ldap_domain", "ldap_admin_username", "ldap_base_dn", "ldap_use_ssl", "sync_schedule", "sync_user_status_schedule"])
        ).all()
        return {s.key: s.value for s in settings}

    def update_settings(self, settings_dict: dict[str, str]) -> None:
        """Bulk update settings."""
        for key, value in settings_dict.items():
            if key == "admin_password_hash":
                continue  # Password changes go through change_password
            if key == "ldap_admin_password" and value == "********":
                continue  # Skip masked values
            setting = self.db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = value
            else:
                self.db.add(Setting(key=key, value=value))
        self.db.commit()

    def change_password(self, current_password: str, new_password: str) -> None:
        """Change admin password."""
        password_setting = self.db.query(Setting).filter(Setting.key == "admin_password_hash").first()
        if not password_setting:
            # Initialize if not exists
            from app.config import settings as app_settings
            self.db.add(Setting(key="admin_password_hash", value=hash_password(app_settings.DEFAULT_ADMIN_PASSWORD)))
            self.db.commit()
            password_setting = self.db.query(Setting).filter(Setting.key == "admin_password_hash").first()

        if not verify_password(current_password, password_setting.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        password_setting.value = hash_password(new_password)
        self.db.commit()

    def get_ldap_config(self) -> dict[str, str]:
        """Get LDAP configuration with actual password value."""
        settings = self.db.query(Setting).filter(Setting.key.like("ldap_%")).all()
        return {s.key.replace("ldap_", ""): s.value for s in settings}
