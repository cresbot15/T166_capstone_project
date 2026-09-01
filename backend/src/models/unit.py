from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.constants import (
    DEFAULT_MAX_GROUP_SIZE,
    DEFAULT_MIN_GROUP_SIZE,
    TIME_SLOT_ORDER,
    UNIT_ROLE_STUDENT,
    UNIT_ROLES,
)
from src.database import Base
from src.services.timestamps import utc_now


class UnitMembership(Base):
    __tablename__ = "user_units"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), primary_key=True)
    role: Mapped[str] = mapped_column(Enum(*UNIT_ROLES, name="unit_role"), default=UNIT_ROLE_STUDENT)

    user = relationship("User", back_populates="unit_memberships")
    unit = relationship("Unit", back_populates="unit_memberships")


class UnitProfile(Base):
    __tablename__ = "user_unit_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), primary_key=True)
    is_new_student: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_mode: Mapped[str | None] = mapped_column(String)
    skills: Mapped[str | None] = mapped_column(String)
    time_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)

    user = relationship("User", back_populates="unit_profiles")
    unit = relationship("Unit", back_populates="unit_profiles")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String)
    min_group_size: Mapped[int] = mapped_column(Integer, default=DEFAULT_MIN_GROUP_SIZE)
    max_group_size: Mapped[int] = mapped_column(Integer, default=DEFAULT_MAX_GROUP_SIZE)
    # None means no limit 0 means no new students are allowed in a group
    max_new_students: Mapped[int | None] = mapped_column(Integer, default=None)
    time_slots: Mapped[list[str]] = mapped_column(JSON, default=lambda: list(TIME_SLOT_ORDER))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    users = relationship("User", secondary="user_units", back_populates="units", viewonly=True)
    unit_memberships = relationship("UnitMembership", back_populates="unit", cascade="all, delete-orphan")
    unit_profiles = relationship("UnitProfile", back_populates="unit", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="unit")
