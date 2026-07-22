from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Computer, User, SyncLog, ADGroup
from app.schemas.dashboard import DashboardStats, RecentActivity
from datetime import datetime, timezone


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> DashboardStats:
        total_computers = self.db.query(func.count(Computer.id)).scalar() or 0
        active_computers = self.db.query(func.count(Computer.id)).filter(Computer.status == "active").scalar() or 0
        disabled_computers = self.db.query(func.count(Computer.id)).filter(Computer.status == "disabled").scalar() or 0
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        total_groups = self.db.query(func.count(ADGroup.id)).scalar() or 0

        # OS distribution
        os_rows = (
            self.db.query(Computer.operating_system, func.count(Computer.id))
            .filter(Computer.operating_system.isnot(None), Computer.operating_system != "")
            .group_by(Computer.operating_system)
            .order_by(func.count(Computer.id).desc())
            .all()
        )
        os_dist = [{"name": r[0], "count": r[1]} for r in os_rows]

        last_sync = (
            self.db.query(SyncLog)
            .filter(SyncLog.status != "running")
            .order_by(SyncLog.completed_at.desc())
            .first()
        )

        return DashboardStats(
            total_computers=total_computers,
            active_computers=active_computers,
            disabled_computers=disabled_computers,
            total_users=total_users,
            total_groups=total_groups,
            last_sync_at=last_sync.completed_at.isoformat() if last_sync and last_sync.completed_at else None,
            last_sync_status=last_sync.status if last_sync else None,
            os_distribution=os_dist,
        )

    def get_recent_activities(self, limit: int = 10) -> list[RecentActivity]:
        """Get recent sync activities."""
        activities = []

        # Recent sync logs
        sync_logs = (
            self.db.query(SyncLog)
            .order_by(SyncLog.started_at.desc())
            .limit(limit)
            .all()
        )
        for log in sync_logs:
            activities.append(
                RecentActivity(
                    id=log.id,
                    activity_type="sync",
                    description=f"{log.sync_type.upper()} Sync",
                    detail=f"{log.records_processed or 0} records processed"
                    if log.status == "success"
                    else log.error_message or "In progress",
                    timestamp=log.started_at.isoformat() if log.started_at else "",
                    status=log.status,
                )
            )

        return activities
