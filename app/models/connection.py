import uuid

from sqlalchemy import Column, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Connection(Base):
    """Таблица связей между дверями"""

    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    door_from = Column(UUID(as_uuid=True), ForeignKey("doors.id", ondelete="CASCADE"), nullable=False)
    door_to = Column(UUID(as_uuid=True), ForeignKey("doors.id", ondelete="CASCADE"), nullable=False)
    distance = Column(Float, nullable=False)
    estimated_time = Column(Float, nullable=True)

    door_from_rel = relationship("Door", foreign_keys=[door_from])
    door_to_rel = relationship("Door", foreign_keys=[door_to])
