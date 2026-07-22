from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.sync_service import SyncService
from app.schemas.sync import SyncLogResponse, SyncStatusResponse
from app.core.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/api/sync", tags=["Sync"])


@router.post("/ldap", response_model=SyncLogResponse)
def trigger_ldap_sync(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Manually trigger an LDAP sync."""
    return SyncService(db).run_ldap_sync()


@router.post("/ldap/user-status", response_model=SyncLogResponse)
def trigger_user_status_sync(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Manually trigger a user-status-only sync (fast, sub-hourly)."""
    return SyncService(db).run_user_status_sync()


@router.get("/logs", response_model=PaginatedResponse[SyncLogResponse])
def list_sync_logs(
    params: PaginationParams = Depends(),
    sync_type: str | None = Query(None, description="ldap|import"),
    status: str | None = Query(None, description="running|success|failed"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return SyncService(db).list_logs(params, sync_type, status)


@router.get("/status", response_model=SyncStatusResponse)
def get_sync_status(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return SyncService(db).get_status()
