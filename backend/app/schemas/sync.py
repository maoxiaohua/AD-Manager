from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SyncLogResponse(BaseModel):
    id: int
    sync_type: str
    status: str
    records_processed: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SyncStatusResponse(BaseModel):
    is_running: bool
    latest_sync: Optional[SyncLogResponse] = None
