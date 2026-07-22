from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.group_service import GroupService
from app.schemas.ad_group import GroupCreate, GroupUpdate, GroupResponse, GroupDetailResponse
from app.core.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/api/groups", tags=["Groups"])


@router.get("/", response_model=PaginatedResponse[GroupResponse])
def list_groups(
    params: PaginationParams = Depends(),
    search: str | None = Query(None, description="Search across name, display name, description"),
    group_type: str | None = Query(None, description="Filter by group type (security/distribution)"),
    group_scope: str | None = Query(None, description="Filter by group scope (domain_local/global/universal)"),
    department: str | None = Query(None, description="Filter by department OU in DN"),
    has_members: bool | None = Query(None, description="Filter: true=with members, false=without members"),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return GroupService(db).list_groups(params, search, group_type, group_scope, department, has_members, sort_by, sort_order)


@router.get("/filter-options")
def get_filter_options(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return GroupService(db).get_filter_options()


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return GroupService(db).get_group(group_id)


@router.get("/{group_id}/detail", response_model=GroupDetailResponse)
def get_group_detail(
    group_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return GroupService(db).get_group_detail(group_id)


@router.post("/", response_model=GroupResponse, status_code=201)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return GroupService(db).create_group(data)


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return GroupService(db).update_group(group_id, data)


@router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    GroupService(db).delete_group(group_id)
