from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserGroupInfo
from app.core.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=PaginatedResponse[UserResponse])
def list_users(
    params: PaginationParams = Depends(),
    search: str | None = Query(None, description="Search across name, email, department"),
    status: str | None = Query(None, alias="status_filter", description="Filter by status: active|disabled|locked"),
    department: str | None = Query(None, description="Filter by department"),
    site: str | None = Query(None, description="Filter by site/city in DN"),
    sort_by: str = Query("sam_account_name"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return UserService(db).list_users(params, search, department, site, sort_by, sort_order, status)


@router.get("/filter-options")
def get_filter_options(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return UserService(db).get_filter_options()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return UserService(db).get_user(user_id)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return UserService(db).create_user(data)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return UserService(db).update_user(user_id, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    UserService(db).delete_user(user_id)


@router.get("/{user_id}/groups", response_model=list[UserGroupInfo])
def get_user_groups(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Get all groups (hostnames) that a user belongs to."""
    return UserService(db).get_user_groups(user_id)


@router.post("/{user_id}/unlock", response_model=UserResponse)
def unlock_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Unlock a locked AD user account."""
    return UserService(db).unlock_user(user_id)
