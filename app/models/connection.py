from sqlalchemy import Column, Float, ForeignKey, Integer

from app.database import Base


class Connection(Base):
    """Таблица связей между дверями"""

    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    door_from = Column(Integer, ForeignKey("doors.id", ondelete="CASCADE"), nullable=False)
    door_to = Column(Integer, ForeignKey("doors.id", ondelete="CASCADE"), nullable=False)
    distance = Column(Float, nullable=False)
    estimated_time = Column(Float, nullable=True)
