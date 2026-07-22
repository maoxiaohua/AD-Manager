from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class GroupMembership(Base):
    """Join table tracking which users belong to which AD groups."""

    __tablename__ = "group_memberships"
    __table_args__ = (
        UniqueConstraint("group_id", "member_dn", name="uq_group_member"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("ad_groups.id"), index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    member_dn: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    group: Mapped["ADGroup"] = relationship("ADGroup", back_populates="memberships")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="group_memberships")

    def __repr__(self) -> str:
        return f"<GroupMembership(group={self.group_id}, member_dn='{self.member_dn}')>"
