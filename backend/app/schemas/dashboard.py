from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_computers: int
    active_computers: int
    disabled_computers: int
    total_users: int
    total_groups: int = 0
    last_sync_at: str | None = None
    last_sync_status: str | None = None
    os_distribution: list[dict] = []


class RecentActivity(BaseModel):
    id: int
    activity_type: str
    description: str
    detail: str
    timestamp: str
    status: str | None = None
