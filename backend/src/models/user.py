from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.constants import USER_ROLE_STUDENT, USER_ROLES
from src.database import Base
from src.services.timestamps import utc_now

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(Enum(*USER_ROLES, name="user_role"), default=USER_ROLE_STUDENT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    units = relationship("Unit", secondary="user_units", back_populates="users", viewonly=True)
    unit_memberships = relationship("UnitMembership", back_populates="user", cascade="all, delete-orphan")
    unit_profiles = relationship("UnitProfile", back_populates="user", cascade="all, delete-orphan")
    groups = relationship("Group", secondary="user_groups", back_populates="members", viewonly=True)
    group_memberships = relationship("GroupMembership", back_populates="user", cascade="all, delete-orphan")
