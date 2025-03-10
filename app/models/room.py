from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Room(Base):
    """Таблица помещений"""

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String(50), unique=True, nullable=False)
    type_id = Column(Integer, ForeignKey("room_types.id", ondelete="SET NULL"), nullable=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)

    floor = relationship("Floor", back_populates="rooms")
    room_type = relationship("RoomType", back_populates="rooms")
    doors = relationship("Door", back_populates="room")
