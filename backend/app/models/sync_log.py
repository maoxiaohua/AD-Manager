from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "ldap" | "import"
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "running" | "success" | "failed"
    records_processed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, type='{self.sync_type}', status='{self.status}')>"
