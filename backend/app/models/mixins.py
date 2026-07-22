from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, ForeignKey, DateTime, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
