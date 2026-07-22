from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<Setting(key='{self.key}')>"
