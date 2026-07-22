from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class Computer(Base, TimestampMixin):
    __tablename__ = "computers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    distinguished_name: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    operating_system: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    last_logon_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Computer(id={self.id}, name='{self.name}')>"
