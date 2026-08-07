from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base


class UnitMembership(Base):
    __tablename__ = "user_units"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String, default="student")

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

    users = relationship("User", secondary="user_units", back_populates="units", viewonly=True)
    unit_memberships = relationship("UnitMembership", back_populates="unit", cascade="all, delete-orphan")
    unit_profiles = relationship("UnitProfile", back_populates="unit", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="unit")
