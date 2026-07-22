from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.computer_service import ComputerService
from app.schemas.computer import ComputerCreate, ComputerUpdate, ComputerResponse
from app.core.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/api/computers", tags=["Computers"])


@router.get("/", response_model=PaginatedResponse[ComputerResponse])
def list_computers(
    params: PaginationParams = Depends(),
    search: str | None = Query(None, description="Search across name, IP, description"),
    status: str | None = Query(None, alias="status_filter", description="Filter by status: active|disabled"),
    department: str | None = Query(None, description="Filter by department OU in DN"),
    operating_system: str | None = Query(None, description="Filter by operating system"),
    stale: bool | None = Query(None, description="Filter: stale computers (90+ days no logon)"),
    sort_by: str = Query("name", description="Sort column"),
    sort_order: str = Query("asc", description="Sort direction: asc|desc"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return ComputerService(db).list_computers(params, search, status, department, operating_system, stale, sort_by, sort_order)


@router.get("/filter-options")
def get_filter_options(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return distinct filter values for dropdowns."""
    return ComputerService(db).get_filter_options()


@router.get("/{computer_id}", response_model=ComputerResponse)
def get_computer(
    computer_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return ComputerService(db).get_computer(computer_id)


@router.post("/", response_model=ComputerResponse, status_code=201)
def create_computer(
    data: ComputerCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return ComputerService(db).create_computer(data)


@router.put("/{computer_id}", response_model=ComputerResponse)
def update_computer(
    computer_id: int,
    data: ComputerUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return ComputerService(db).update_computer(computer_id, data)


@router.delete("/{computer_id}", status_code=204)
def delete_computer(
    computer_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    ComputerService(db).delete_computer(computer_id)
