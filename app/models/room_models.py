# models/room_models.py

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    room_code: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
        unique=True,
        index=True
    )

    # Human-friendly name for the room
    room_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False
    )

    starting_roll: Mapped[str] = mapped_column(String, nullable=False)
    ending_roll: Mapped[str] = mapped_column(String, nullable=False)

    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # 🔹 Teacher relationship (one-to-many)
    teacher = relationship("Teacher", back_populates="rooms")

    # 🔥 AttendanceToken relationship (room ↔ student bridge)
    tokens = relationship(
        "AttendanceToken",
        back_populates="room",
        cascade="all, delete-orphan"
    )