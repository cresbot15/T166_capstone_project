from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class UnitMembership(Base):
    __tablename__ = "user_units"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id"), primary_key=True)
    role = Column(String, nullable=False, default="student")

    user = relationship("User", back_populates="unit_memberships")
    unit = relationship("Unit", back_populates="unit_memberships")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)

    users = relationship("User", secondary="user_units", back_populates="units", viewonly=True)
    unit_memberships = relationship("UnitMembership", back_populates="unit", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="unit")
