from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GroupBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    distinguished_name: str
    group_type: str = "security"
    group_scope: str = "global"
    description: Optional[str] = None
    email: Optional[str] = None
    # Optional extension fields (rename for your organization)
    end_user_email: Optional[str] = None
    jira_ticket: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    group_type: Optional[str] = None
    group_scope: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    # Optional extension fields (rename for your organization)
    end_user_email: Optional[str] = None
    jira_ticket: Optional[str] = None


class GroupResponse(GroupBase):
    id: int
    member_count: int = 0
    # Optional extension fields (rename for your organization)
    end_user_email: Optional[str] = None
    jira_ticket: Optional[str] = None
    assigned_at: Optional[datetime] = None
    site: Optional[str] = None
    department: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GroupMemberInfo(BaseModel):
    """Simplified member info for group detail view."""
    id: int
    member_dn: str
    user_id: Optional[int] = None
    sam_account_name: Optional[str] = None
    display_name: Optional[str] = None


class GroupDetailResponse(GroupResponse):
    members: list[GroupMemberInfo] = []
