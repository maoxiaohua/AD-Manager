from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and seed default settings. Called at application startup."""
    # Import all models so they register with Base.metadata
    import app.models.computer  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.sync_log  # noqa: F401
    import app.models.setting  # noqa: F401
    import app.models.ad_group  # noqa: F401
    import app.models.group_membership  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # ── Clean up orphaned sync records from a previous crash ──
    import logging
    from datetime import datetime, timezone
    _db_logger = logging.getLogger("database")
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "UPDATE sync_logs SET status='failed', "
                "error_message='Server restarted while sync was in progress', "
                "completed_at=:now WHERE status IN ('running', 'pending')"
            ),
            {"now": datetime.now(timezone.utc)},
        )
        conn.commit()
        if result.rowcount > 0:
            _db_logger.warning(
                f"Cleaned up {result.rowcount} orphaned sync log(s) from previous run"
            )

    # ── Migrations for existing columns ──
    from sqlalchemy import inspect
    with engine.connect() as conn:
        insp = inspect(conn)
        if "users" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("users")}
            if "bad_pwd_count" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN bad_pwd_count INTEGER"))
                conn.commit()

    # Seed default admin password if not exists
    from app.core.security import hash_password
    from app.models.setting import Setting
    from app.config import settings as app_settings
    db = SessionLocal()
    try:
        existing = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
        if not existing:
            db.add(Setting(key="admin_password_hash", value=hash_password(app_settings.DEFAULT_ADMIN_PASSWORD)))
            db.commit()
    finally:
        db.close()
