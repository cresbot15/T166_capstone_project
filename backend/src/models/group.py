from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.services.requirements import evaluate_group


class GroupMembership(Base):
    __tablename__ = "user_groups"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), primary_key=True)

    user = relationship("User", back_populates="group_memberships")
    group = relationship("Group", back_populates="group_memberships")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    preference_code: Mapped[str | None] = mapped_column(String, unique=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    creator_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    unit = relationship("Unit", back_populates="groups")
    creator_user = relationship("User", foreign_keys=[creator_user_id])
    members = relationship("User", secondary="user_groups", back_populates="groups", viewonly=True)
    group_memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")

    @property
    def common_time_slots(self) -> list[str]:
        if not self.members:
            return []
        sets = []
        for m in self.members:
            profile = next((p for p in m.unit_profiles if p.unit_id == self.unit_id), None)
            sets.append(set(profile.time_preferences if profile else []))
        result = sets[0]
        for s in sets[1:]:
            result = result & s
        return sorted(result)

    @property
    def unmet_requirements(self) -> list[str]:
        return evaluate_group(self, self.unit)

    @property
    def status(self) -> str:
        return "provisional" if self.unmet_requirements else "pending"
