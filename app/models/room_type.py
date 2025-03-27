import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RoomType(Base):
    """Таблица типов помещений"""

    __tablename__ = "room_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type_name = Column(String(100), unique=True, nullable=False)

    rooms = relationship("Room", back_populates="room_type")
