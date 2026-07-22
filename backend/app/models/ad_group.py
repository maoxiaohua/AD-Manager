from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class ADGroup(Base, TimestampMixin):
    """AD security or distribution group synced from Active Directory."""

    __tablename__ = "ad_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    distinguished_name: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    group_type: Mapped[str] = mapped_column(String(20), default="security", nullable=False)
    group_scope: Mapped[str] = mapped_column(String(20), default="global", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # --- Optional extension fields (rename for your organization) ---
    end_user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    jira_ticket: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    memberships: Mapped[List["GroupMembership"]] = relationship(
        "GroupMembership", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ADGroup(id={self.id}, name='{self.name}')>"
