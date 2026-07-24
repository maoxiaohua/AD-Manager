import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AD Hostname Manager"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-me-to-a-random-secret-string"
    DATABASE_URL: str = "sqlite:///./ad_manager.db"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    CORS_ORIGINS: list[str] = ["*"]  # Override in .env for production: ["http://frontend:3000"]

    # LDAP TLS validation mode: CERT_NONE, CERT_OPTIONAL, or CERT_REQUIRED
    LDAP_TLS_VALIDATE: str = "CERT_NONE"

    # LDAP defaults (overridden by settings table at runtime)
    LDAP_SERVER_URL: str = ""
    LDAP_DOMAIN: str = ""
    LDAP_ADMIN_USERNAME: str = ""
    LDAP_ADMIN_PASSWORD: str = ""
    LDAP_BASE_DN: str = ""
    LDAP_USE_SSL: str = "true"
    LDAP_PAGE_SIZE: int = 500
    LDAP_RECEIVE_TIMEOUT: int = 300
    LOCATION_BASE_OU: str = ""  # Parent OU for city location discovery (e.g. "OU=locations")

    # Sync tuning
    LOCKOUT_THRESHOLD: int = 5
    SYNC_MISFIRE_GRACE: int = 300     # seconds for full sync job
    USER_STATUS_MISFIRE_GRACE: int = 120  # seconds for user-status sync job
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"

    SYNC_SCHEDULE: str = "0 2 * * *"
    SYNC_LOG_RETENTION_DAYS: int = 30  # Auto-delete sync logs older than this

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Validate critical security defaults at import time
import logging
_logger = logging.getLogger("config")
if settings.SECRET_KEY == "change-me-to-a-random-secret-string":
    _logger.warning(
        "SECURITY: SECRET_KEY is set to the default value. "
        "Generate a random key for production (e.g., openssl rand -hex 32)."
    )
