import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal

logger = logging.getLogger("scheduler")

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler


def _scheduled_ldap_sync_wrapper():
    """Runs in a background thread. Creates its own DB session."""
    from app.services.sync_service import SyncService
    from app.models import Setting

    db = SessionLocal()
    try:
        # Check schedule from settings
        schedule = db.query(Setting).filter(Setting.key == "sync_schedule").first()
        if schedule and schedule.value == "disabled":
            return  # Sync is disabled via settings

        SyncService(db).run_ldap_sync()
    except Exception:
        logger.exception("Scheduled LDAP sync raised an unhandled exception")
    finally:
        db.close()


def _scheduled_user_status_sync_wrapper():
    """Runs in a background thread. Syncs only user status at sub-hourly cadence."""
    from app.services.sync_service import SyncService
    from app.models import Setting

    db = SessionLocal()
    try:
        schedule = db.query(Setting).filter(Setting.key == "sync_user_status_schedule").first()
        if schedule and schedule.value == "disabled":
            return

        SyncService(db).run_user_status_sync()
    except Exception:
        logger.exception("Scheduled user-status sync raised an unhandled exception")
    finally:
        db.close()


def init_scheduler():
    global _scheduler
    if _scheduler is not None:
        return

    from app.config import settings
    from app.models import Setting

    # Read schedule: DB first, then config, then default
    cron_expr = settings.SYNC_SCHEDULE or "0 2 * * *"
    try:
        db = SessionLocal()
        row = db.query(Setting).filter(Setting.key == "sync_schedule").first()
        if row and row.value:
            cron_expr = row.value
        db.close()
    except Exception:
        logger.warning("Could not read sync_schedule from DB, using default", exc_info=True)

    _scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)
    _scheduler.add_job(
        _scheduled_ldap_sync_wrapper,
        trigger=CronTrigger.from_crontab(cron_expr),
        id="ldap_sync_job",
        replace_existing=True,
        misfire_grace_time=settings.SYNC_MISFIRE_GRACE,
    )

    # User-status sync: lightweight, every 5 min by default
    user_status_cron = "*/5 * * * *"
    try:
        db = SessionLocal()
        row = db.query(Setting).filter(Setting.key == "sync_user_status_schedule").first()
        if row and row.value:
            user_status_cron = row.value
        db.close()
    except Exception:
        pass

    _scheduler.add_job(
        _scheduled_user_status_sync_wrapper,
        trigger=CronTrigger.from_crontab(user_status_cron),
        id="ldap_user_status_sync_job",
        replace_existing=True,
        misfire_grace_time=settings.USER_STATUS_MISFIRE_GRACE,
    )

    _scheduler.start()


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def update_schedule(cron_expression: str, job_id: str = "ldap_sync_job"):
    """Update a sync schedule dynamically. Accepts job_id to target the right job."""
    global _scheduler
    if _scheduler:
        if cron_expression == "disabled":
            _scheduler.pause_job(job_id)
        else:
            _scheduler.reschedule_job(
                job_id,
                trigger=CronTrigger.from_crontab(cron_expression),
            )
            _scheduler.resume_job(job_id)
