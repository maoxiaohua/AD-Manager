from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin
from datetime import datetime


class User(Base, TimestampMixin):
    """AD domain user (not system auth user)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sam_account_name: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    distinguished_name: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    user_account_control: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    uac_flags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    lockout_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bad_pwd_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    group_memberships: Mapped[List["GroupMembership"]] = relationship(
        "GroupMembership", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, sam='{self.sam_account_name}')>"
