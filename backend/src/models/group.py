from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.constants import GROUP_LIFECYCLE_ACTIVE, GROUP_LIFECYCLES
from src.database import Base
from src.models.types import UtcDateTime
from src.services.availability import common_time_slots
from src.services.requirements import evaluate_group
from src.services.timestamps import utc_now


class GroupMembership(Base):
    __tablename__ = "user_groups"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), primary_key=True)

    user = relationship("User", back_populates="group_memberships")
    group = relationship("Group", back_populates="group_memberships")


class Group(Base):
    __tablename__ = "groups"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    preference_code: Mapped[str | None] = mapped_column(String, unique=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    creator_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    lifecycle: Mapped[str] = mapped_column(
        Enum(*GROUP_LIFECYCLES, name="group_lifecycle"), default=GROUP_LIFECYCLE_ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    unit = relationship("Unit", back_populates="groups")
    creator_user = relationship("User", foreign_keys=[creator_user_id])
    members = relationship("User", secondary="user_groups", back_populates="groups", viewonly=True)
    group_memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")

    @property
    def common_time_slots(self) -> list[str]:
        return common_time_slots(self.members, self.unit_id)

    @property
    def unmet_requirements(self) -> list[str]:
        return evaluate_group(self, self.unit)

    @property
    def status(self) -> str:
        return "provisional" if self.unmet_requirements else "pending"
