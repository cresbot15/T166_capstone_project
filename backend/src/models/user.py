from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)

    units = relationship("Unit", secondary="user_units", back_populates="users", viewonly=True)
    unit_memberships = relationship("UnitMembership", back_populates="user", cascade="all, delete-orphan")
    unit_profiles = relationship("UnitProfile", back_populates="user", cascade="all, delete-orphan")
    groups = relationship("Group", secondary="user_groups", back_populates="members", viewonly=True)
    group_memberships = relationship("GroupMembership", back_populates="user", cascade="all, delete-orphan")
