from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardStats, RecentActivity

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return DashboardService(db).get_stats()


@router.get("/recent-activities", response_model=list[RecentActivity])
def get_recent_activities(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return DashboardService(db).get_recent_activities(limit)
