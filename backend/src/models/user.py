from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.unit import user_units
from src.models.group import user_groups

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_new_student = Column(Boolean, nullable=False, default=False)
    delivery_mode = Column(String, nullable=True)
    skills = Column(String, nullable=True)
    time_preferences = Column(JSON, nullable=False, default=list)
    
    units = relationship("Unit", secondary=user_units, back_populates="users")
    groups = relationship("Group", secondary=user_groups, back_populates="members")

    @property
    def group_ids(self) -> list[int]:
        return [g.id for g in self.groups]