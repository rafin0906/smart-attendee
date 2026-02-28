# models/attendance_token_models.py
import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AttendanceToken(Base):
    __tablename__ = "attendance_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )

    roll_no: Mapped[str] = mapped_column(String, nullable=False)

    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    fingerprint_token: Mapped[str | None] = mapped_column(String, nullable=True)

    assigned_student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
    )

    used: Mapped[bool] = mapped_column(Boolean, default=False)

    room = relationship("Room", back_populates="tokens")
    student = relationship("Student", back_populates="attendance_tokens")
