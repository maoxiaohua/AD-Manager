from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ComputerBase(BaseModel):
    name: str
    distinguished_name: str
    ip_address: Optional[str] = None
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    status: Literal["active", "disabled"] = "active"


class ComputerCreate(ComputerBase):
    pass


class ComputerUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["active", "disabled"]] = None


class ComputerResponse(ComputerBase):
    id: int
    site: Optional[str] = None
    department: Optional[str] = None
    days_since_logon: Optional[int] = None
    last_logon_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
