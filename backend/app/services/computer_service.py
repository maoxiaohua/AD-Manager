from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Computer
from app.schemas.computer import ComputerCreate, ComputerUpdate, ComputerResponse
from app.core.pagination import PaginatedResponse, PaginationParams
from app.core.dn_parser import parse_dn
from fastapi import HTTPException, status


class ComputerService:
    def __init__(self, db: Session):
        self.db = db

    def list_computers(
        self,
        params: PaginationParams,
        search: str | None = None,
        status_filter: str | None = None,
        department: str | None = None,
        operating_system: str | None = None,
        stale: bool | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> PaginatedResponse[ComputerResponse]:
        query = self.db.query(Computer)

        if search:
            query = query.filter(
                or_(
                    Computer.name.ilike(f"%{search}%"),
                    Computer.ip_address.ilike(f"%{search}%"),
                    Computer.description.ilike(f"%{search}%"),
                    Computer.distinguished_name.ilike(f"%{search}%"),
                )
            )
        if status_filter:
            query = query.filter(Computer.status == status_filter)
        if department:
            query = query.filter(Computer.distinguished_name.ilike(f"%OU={department}%"))
        if operating_system:
            query = query.filter(Computer.operating_system.ilike(f"%{operating_system}%"))

        if stale:
            from datetime import datetime, timezone, timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            query = query.filter(
                (Computer.last_logon_timestamp < cutoff)
                | (Computer.last_logon_timestamp.is_(None))
            )

        sort_col = getattr(Computer, sort_by, Computer.name)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        total = query.count()
        computers = query.offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        items = [self._to_response(c) for c in computers]
        return PaginatedResponse.from_query(items, total, params)

    def get_computer(self, computer_id: int) -> ComputerResponse:
        computer = self._get_or_404(computer_id)
        return self._to_response(computer)

    def create_computer(self, data: ComputerCreate) -> ComputerResponse:
        computer = Computer(
            name=data.name,
            distinguished_name=data.distinguished_name,
            ip_address=data.ip_address,
            operating_system=data.operating_system,
            os_version=data.os_version,
            description=data.description,
            status=data.status,
        )
        self.db.add(computer)
        self.db.commit()
        self.db.refresh(computer)
        return self._to_response(computer)

    def update_computer(self, computer_id: int, data: ComputerUpdate) -> ComputerResponse:
        computer = self._get_or_404(computer_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(computer, key, value)
        self.db.commit()
        self.db.refresh(computer)
        return self._to_response(computer)

    def delete_computer(self, computer_id: int) -> None:
        computer = self._get_or_404(computer_id)
        self.db.delete(computer)
        self.db.commit()

    def _to_response(self, computer: Computer) -> ComputerResponse:
        dn_info = parse_dn(computer.distinguished_name)
        days_since_logon = None
        if computer.last_logon_timestamp:
            from datetime import datetime, timezone
            delta = datetime.now(timezone.utc) - computer.last_logon_timestamp
            days_since_logon = delta.days
        return ComputerResponse(
            id=computer.id,
            name=computer.name,
            distinguished_name=computer.distinguished_name,
            ip_address=computer.ip_address,
            operating_system=computer.operating_system,
            os_version=computer.os_version,
            description=computer.description,
            status=computer.status,
            site=dn_info["site"] or None,
            department=dn_info["department"] or None,
            days_since_logon=days_since_logon,
            last_logon_timestamp=computer.last_logon_timestamp,
            created_at=computer.created_at,
            updated_at=computer.updated_at,
        )

    def _get_or_404(self, computer_id: int) -> Computer:
        computer = self.db.query(Computer).filter(Computer.id == computer_id).first()
        if not computer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Computer {computer_id} not found")
        return computer

    def get_filter_options(self) -> dict:
        """Return distinct filter values for dropdowns."""
        from app.core.dn_parser import parse_dn

        # OS values from direct column
        os_values = sorted(set(
            r[0] for r in self.db.query(Computer.operating_system)
            .filter(Computer.operating_system.isnot(None), Computer.operating_system != "")
            .distinct().all()
        ))

        # Department and site from DN parsing
        departments = set()
        sites = set()
        for (dn,) in self.db.query(Computer.distinguished_name).all():
            info = parse_dn(dn)
            if info["department"]:
                departments.add(info["department"])
            if info["site"]:
                sites.add(info["site"])

        return {
            "operating_systems": os_values,
            "departments": sorted(departments),
            "sites": sorted(sites),
        }
