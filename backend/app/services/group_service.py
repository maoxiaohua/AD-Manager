from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import ADGroup, GroupMembership, User
from app.schemas.ad_group import (
    GroupCreate, GroupUpdate, GroupResponse,
    GroupDetailResponse, GroupMemberInfo,
)
from app.core.pagination import PaginatedResponse, PaginationParams
from app.core.dn_parser import parse_dn
from fastapi import HTTPException, status
from math import ceil


class GroupService:
    def __init__(self, db: Session):
        self.db = db

    def list_groups(
        self,
        params: PaginationParams,
        search: str | None = None,
        group_type: str | None = None,
        group_scope: str | None = None,
        department: str | None = None,
        has_members: bool | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> PaginatedResponse[GroupResponse]:
        query = self.db.query(ADGroup)

        if search:
            query = query.filter(
                or_(
                    ADGroup.name.ilike(f"%{search}%"),
                    ADGroup.display_name.ilike(f"%{search}%"),
                    ADGroup.description.ilike(f"%{search}%"),
                )
            )
        if group_type:
            query = query.filter(ADGroup.group_type == group_type)
        if group_scope:
            query = query.filter(ADGroup.group_scope == group_scope)
        if department:
            query = query.filter(ADGroup.distinguished_name.ilike(f"%OU={department}%"))

        if has_members is not None:
            subquery = (
                self.db.query(GroupMembership.group_id)
                .filter(GroupMembership.user_id.isnot(None))
                .distinct()
                .subquery()
            )
            if has_members:
                query = query.filter(ADGroup.id.in_(subquery))
            else:
                query = query.filter(ADGroup.id.notin_(subquery))

        sort_col = getattr(ADGroup, sort_by, ADGroup.name)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        total = query.count()
        groups = query.offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        items = [self._to_response(g) for g in groups]
        return PaginatedResponse.from_query(items, total, params)

    def get_group(self, group_id: int) -> GroupResponse:
        group = self._get_or_404(group_id)
        return self._to_response(group)

    def get_group_detail(self, group_id: int) -> GroupDetailResponse:
        group = self._get_or_404(group_id)
        return self._to_detail_response(group)

    def create_group(self, data: GroupCreate) -> GroupResponse:
        group = ADGroup(
            name=data.name,
            display_name=data.display_name,
            distinguished_name=data.distinguished_name,
            group_type=data.group_type,
            group_scope=data.group_scope,
            description=data.description,
            email=data.email,
            end_user_email=data.end_user_email,
            jira_ticket=data.jira_ticket,
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return self._to_response(group)

    def update_group(self, group_id: int, data: GroupUpdate) -> GroupResponse:
        group = self._get_or_404(group_id)
        update_data = data.model_dump(exclude_unset=True)
        # Auto-set assigned_at when end_user_email is first set
        if "end_user_email" in update_data:
            new_email = update_data["end_user_email"]
            if new_email and not group.end_user_email:
                from datetime import datetime, timezone
                update_data["assigned_at"] = datetime.now(timezone.utc)
            elif not new_email:
                update_data["assigned_at"] = None
        for key, value in update_data.items():
            setattr(group, key, value)
        self.db.commit()
        self.db.refresh(group)
        return self._to_response(group)

    def delete_group(self, group_id: int) -> None:
        group = self._get_or_404(group_id)
        self.db.delete(group)
        self.db.commit()

    def _to_response(self, group: ADGroup) -> GroupResponse:
        member_count = (
            self.db.query(GroupMembership)
            .filter(GroupMembership.group_id == group.id)
            .count()
        )
        dn_info = parse_dn(group.distinguished_name)

        return GroupResponse(
            id=group.id,
            name=group.name,
            display_name=group.display_name,
            distinguished_name=group.distinguished_name,
            group_type=group.group_type,
            group_scope=group.group_scope,
            description=group.description,
            email=group.email,
            member_count=member_count,
            end_user_email=group.end_user_email,
            jira_ticket=group.jira_ticket,
            assigned_at=group.assigned_at,
            site=dn_info["site"] or None,
            department=dn_info["department"] or None,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    def _to_detail_response(self, group: ADGroup) -> GroupDetailResponse:
        base = self._to_response(group)
        memberships = (
            self.db.query(GroupMembership)
            .filter(GroupMembership.group_id == group.id)
            .all()
        )
        members = []
        for m in memberships:
            user = self.db.query(User).filter(User.id == m.user_id).first() if m.user_id else None
            members.append(
                GroupMemberInfo(
                    id=m.id,
                    member_dn=m.member_dn,
                    user_id=m.user_id,
                    sam_account_name=user.sam_account_name if user else None,
                    display_name=user.display_name if user else None,
                )
            )

        return GroupDetailResponse(
            id=base.id,
            name=base.name,
            display_name=base.display_name,
            distinguished_name=base.distinguished_name,
            group_type=base.group_type,
            group_scope=base.group_scope,
            description=base.description,
            email=base.email,
            member_count=base.member_count,
            created_at=base.created_at,
            updated_at=base.updated_at,
            members=members,
        )

    def _get_or_404(self, group_id: int) -> ADGroup:
        group = self.db.query(ADGroup).filter(ADGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {group_id} not found")
        return group

    def get_filter_options(self) -> dict:
        from app.core.dn_parser import parse_dn
        departments = set()
        sites = set()
        for (dn,) in self.db.query(ADGroup.distinguished_name).all():
            info = parse_dn(dn)
            if info["department"]:
                departments.add(info["department"])
            if info["site"]:
                sites.add(info["site"])
        return {
            "departments": sorted(departments),
            "sites": sorted(sites),
        }
