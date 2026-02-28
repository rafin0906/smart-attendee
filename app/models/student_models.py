# models/student_models.py

import uuid
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base 


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    full_name: Mapped[str] = mapped_column(String, nullable=False)

    roll_no: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # 🔥 Relationship via AttendanceToken (many-to-many)
    attendance_tokens = relationship(
        "AttendanceToken",
        back_populates="student",
        cascade="all, delete"
    )