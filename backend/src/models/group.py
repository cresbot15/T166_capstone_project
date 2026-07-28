from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    preference_code = Column(String, unique=True, nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    creator_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    unit = relationship("Unit", back_populates="groups")
    creator_user = relationship("User", foreign_keys=[creator_user_id])
    members = relationship("User", secondary=user_groups, back_populates="groups")

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
