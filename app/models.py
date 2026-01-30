from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
import enum

from app.database import Base


class WidgetStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Widget(Base):
    __tablename__ = "widgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    complexity_score = Column(Integer, nullable=False)
    status = Column(
        Enum(WidgetStatus),
        nullable=False,
        default=WidgetStatus.PENDING
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Widget(id={self.id}, name='{self.name}', status='{self.status}')>"
