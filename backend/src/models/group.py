from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base


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

    unit = relationship("Unit", back_populates="groups")
    creator_user = relationship("User", foreign_keys=[creator_user_id])
    members = relationship("User", secondary="user_groups", back_populates="groups", viewonly=True)
    group_memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")

    @property
    def common_time_slots(self) -> list[str]:
        if not self.members:
            return []
        sets = [set(m.time_preferences or []) for m in self.members]
        result = sets[0]
        for s in sets[1:]:
            result = result & s
        return sorted(result)

    @property
    def status(self) -> str:
        return "valid" if self.common_time_slots else "provisional"
