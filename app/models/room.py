import uuid

from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Room(Base):
    """Таблица помещений"""

    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id = Column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String(50), unique=True, nullable=False)
    type_id = Column(UUID(as_uuid=True), ForeignKey("room_types.id", ondelete="SET NULL"), nullable=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)

    floor = relationship("Floor", back_populates="rooms")
    room_type = relationship("RoomType", back_populates="rooms")
    doors = relationship("Door", back_populates="room")
