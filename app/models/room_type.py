from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class RoomType(Base):
    """Таблица типов помещений"""

    __tablename__ = "room_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(100), unique=True, nullable=False)

    rooms = relationship("Room", back_populates="room_type")
