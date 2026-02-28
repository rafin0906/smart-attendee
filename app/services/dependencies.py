# app/services/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import os
import uuid

from app.database import get_db
from app.models.session_models import Session as UserSession
from app.models.teacher_models import Teacher
from app.models.student_models import Student

security = HTTPBearer()


def get_current_teacher(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Teacher:

    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("SECRET_KEY"),
            algorithms=["HS256"],
        )

        token_type = payload.get("type")
        if token_type and token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        teacher_id = payload.get("sub")
        sid = payload.get("sid")

        if not teacher_id or not sid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        try:
            teacher_uuid = uuid.UUID(str(teacher_id))
            session_uuid = uuid.UUID(str(sid))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Immediate logout on other device: session must still exist
        session_obj = (
            db.query(UserSession)
            .filter(
                UserSession.id == session_uuid,
                UserSession.user_id == teacher_uuid,
            )
            .first()
        )

        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or logged in on another device",
            )

        teacher = db.query(Teacher).filter(Teacher.id == teacher_uuid).first()

        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Teacher not found"
            )

        return teacher

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Student:

    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("SECRET_KEY"),
            algorithms=["HS256"],
        )

        token_type = payload.get("type")
        if token_type and token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        student_id = payload.get("sub")
        sid = payload.get("sid")

        if not student_id or not sid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        try:
            student_uuid = uuid.UUID(str(student_id))
            session_uuid = uuid.UUID(str(sid))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        session_obj = (
            db.query(UserSession)
            .filter(
                UserSession.id == session_uuid,
                UserSession.user_id == student_uuid,
            )
            .first()
        )

        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or logged in on another device",
            )

        student = db.query(Student).filter(Student.id == student_uuid).first()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Student not found"
            )

        return student

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
