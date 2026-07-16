from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    preference_code = Column(String, unique=True, nullable=True)
    members = relationship("User", back_populates="group")

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
