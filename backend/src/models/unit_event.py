from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.constants import EVENT_TYPES
from src.database import Base
from src.services.timestamps import utc_now


class UnitEvent(Base):
    __tablename__ = "unit_events"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    event_type: Mapped[str] = mapped_column(Enum(*EVENT_TYPES, name="event_type"), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    subject_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), index=True)

    detail: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    unit = relationship("Unit")
    actor_user = relationship("User", foreign_keys=[actor_user_id])
    subject_user = relationship("User", foreign_keys=[subject_user_id])

    @property
    def actor_name(self) -> str | None:
        return f"{self.actor_user.first_name} {self.actor_user.last_name}" if self.actor_user else None

    @property
    def subject_name(self) -> str | None:
        return f"{self.subject_user.first_name} {self.subject_user.last_name}" if self.subject_user else None
