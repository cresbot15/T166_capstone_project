from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_new_student: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_mode: Mapped[str | None] = mapped_column(String)
    skills: Mapped[str | None] = mapped_column(String)
    time_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)

    units = relationship("Unit", secondary="user_units", back_populates="users", viewonly=True)
    unit_memberships = relationship("UnitMembership", back_populates="user", cascade="all, delete-orphan")
    groups = relationship("Group", secondary="user_groups", back_populates="members", viewonly=True)
    group_memberships = relationship("GroupMembership", back_populates="user", cascade="all, delete-orphan")
