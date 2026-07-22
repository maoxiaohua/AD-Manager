from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    sam_account_name: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    distinguished_name: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    sam_account_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None


class UserResponse(UserBase):
    id: int
    group_count: int = 0
    site: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    uac_flags: Optional[str] = None
    lockout_time: Optional[datetime] = None
    bad_pwd_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserGroupInfo(BaseModel):
    group_id: int
    group_name: str
    group_type: str
    description: Optional[str] = None
