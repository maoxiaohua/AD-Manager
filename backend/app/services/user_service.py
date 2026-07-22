from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import User, GroupMembership, ADGroup, Setting
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserGroupInfo
from app.core.pagination import PaginatedResponse, PaginationParams
from app.core.dn_parser import parse_dn
from fastapi import HTTPException, status


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def list_users(
        self,
        params: PaginationParams,
        search: str | None = None,
        department: str | None = None,
        site: str | None = None,
        sort_by: str = "sam_account_name",
        sort_order: str = "asc",
        status: str | None = None,
    ) -> PaginatedResponse[UserResponse]:
        query = self.db.query(User)

        if search:
            query = query.filter(
                or_(
                    User.sam_account_name.ilike(f"%{search}%"),
                    User.display_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.department.ilike(f"%{search}%"),
                )
            )
        if status:
            query = query.filter(User.status == status)
        if department:
            query = query.filter(User.department == department)
        if site:
            query = query.filter(User.distinguished_name.ilike(f"%OU={site}%"))

        sort_col = getattr(User, sort_by, User.sam_account_name)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        total = query.count()
        users = query.offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        items = [self._to_response(u) for u in users]
        return PaginatedResponse.from_query(items, total, params)

    def get_user(self, user_id: int) -> UserResponse:
        user = self._get_or_404(user_id)
        return self._to_response(user)

    def create_user(self, data: UserCreate) -> UserResponse:
        user = User(
            sam_account_name=data.sam_account_name,
            display_name=data.display_name,
            email=data.email,
            department=data.department,
            distinguished_name=data.distinguished_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_response(user)

    def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        user = self._get_or_404(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return self._to_response(user)

    def delete_user(self, user_id: int) -> None:
        user = self._get_or_404(user_id)
        self.db.delete(user)
        self.db.commit()

    def unlock_user(self, user_id: int) -> UserResponse:
        user = self._get_or_404(user_id)
        if user.status != "locked":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not locked",
            )

        from app.ldap_client import LDAPClient, LDAPConfig

        settings = {s.key: s.value for s in self.db.query(Setting).filter(Setting.key.like("ldap_%")).all()}
        ldap_config = LDAPConfig(
            server_url=settings.get("ldap_server_url", "ldaps://localhost:636"),
            domain=settings.get("ldap_domain", ""),
            admin_username=settings.get("ldap_admin_username", ""),
            admin_password=settings.get("ldap_admin_password", ""),
            base_dn=settings.get("ldap_base_dn", ""),
            use_ssl=settings.get("ldap_use_ssl", "true").lower() == "true",
        )

        try:
            with LDAPClient(ldap_config) as client:
                if not client.unlock_user(user.distinguished_name):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="AD unlock failed: LDAP modify returned non-zero result",
                    )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AD unlock failed: {e}",
            )

        user.status = "active"
        user.lockout_time = None
        user.bad_pwd_count = 0
        self.db.commit()
        self.db.refresh(user)
        return self._to_response(user)

    def _to_response(self, user: User) -> UserResponse:
        group_count = (
            self.db.query(GroupMembership)
            .filter(GroupMembership.user_id == user.id)
            .count()
        )
        dn_info = parse_dn(user.distinguished_name)
        return UserResponse(
            id=user.id,
            sam_account_name=user.sam_account_name,
            display_name=user.display_name,
            email=user.email,
            department=user.department,
            distinguished_name=user.distinguished_name,
            group_count=group_count,
            site=dn_info["site"] or None,
            status=user.status,
            uac_flags=user.uac_flags,
            lockout_time=user.lockout_time,
            bad_pwd_count=user.bad_pwd_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def get_user_groups(self, user_id: int) -> list[UserGroupInfo]:
        user = self._get_or_404(user_id)
        memberships = (
            self.db.query(GroupMembership)
            .filter(GroupMembership.user_id == user.id)
            .all()
        )
        result = []
        for m in memberships:
            group = self.db.query(ADGroup).filter(ADGroup.id == m.group_id).first()
            if group:
                result.append(UserGroupInfo(
                    group_id=group.id,
                    group_name=group.name,
                    group_type=group.group_type,
                    description=group.description,
                ))
        return result

    def _get_or_404(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
        return user

    def get_filter_options(self) -> dict:
        from app.core.dn_parser import parse_dn
        departments = set()
        sites = set()
        for (dn,) in self.db.query(User.distinguished_name).all():
            info = parse_dn(dn)
            if info["department"]:
                departments.add(info["department"])
            if info["site"]:
                sites.add(info["site"])
        return {
            "departments": sorted(departments),
            "sites": sorted(sites),
        }
