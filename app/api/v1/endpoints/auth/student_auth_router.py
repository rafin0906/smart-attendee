from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.student_models import Student
from app.models.session_models import Session as UserSession
from app.schemas.student_schema import (
    StudentCreate,
    StudentLogin,
    StudentResponse,
    StudentAuthResponse,
)

from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.jwt import SECRET_KEY, ALGORITHM
from jose import jwt
from pydantic import BaseModel

router = APIRouter(prefix="/student", tags=["Student Auth"])


# ✅ SIGN UP
@router.post("/sign_up", response_model=StudentResponse)
def student_sign_up(payload: StudentCreate, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.email == payload.email).first()

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_student = Student(
        full_name=payload.full_name,
        roll_no=payload.roll_no,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


# ✅ SIGN IN
@router.post("/sign_in", response_model=StudentAuthResponse)
def student_sign_in(
    payload: StudentLogin, db: Session = Depends(get_db)
) -> StudentAuthResponse:
    student = db.query(Student).filter(Student.email == payload.email).first()

    if not student or not verify_password(payload.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # 🔥 Single-device login: remove ALL previous sessions of this user
    db.query(UserSession).filter(UserSession.user_id == student.id).delete()
    db.commit()

    session_id = uuid.uuid4()
    refresh_token = create_refresh_token(
        {"sub": str(student.id), "sid": str(session_id), "user_type": "student"}
    )

    new_session = UserSession(
        id=session_id,
        user_id=student.id,
        device_id=payload.device_id,
        refresh_token=refresh_token,
    )
    db.add(new_session)
    db.commit()

    access_token = create_access_token(
        {"sub": str(student.id), "sid": str(session_id), "user_type": "student"}
    )

    return {
        "user": student,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


class RefreshTokenPayload(BaseModel):
    refresh_token: str


@router.post("/refresh")
def student_refresh_token(payload: RefreshTokenPayload, db: Session = Depends(get_db)):
    refresh_token = payload.refresh_token

    # validate jwt
    try:
        token_data = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = token_data.get("sub")
        sid = token_data.get("sid")
        token_type = token_data.get("type")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if token_type and token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if not sid or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    try:
        sid_uuid = uuid.UUID(str(sid))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # find session by sid + refresh_token (rotation-safe)
    session_obj = (
        db.query(UserSession)
        .filter(UserSession.id == sid_uuid, UserSession.refresh_token == refresh_token)
        .first()
    )

    if not session_obj or str(session_obj.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or another device logged in with this account",
        )

    # issue new tokens (rotate refresh token)
    new_refresh = create_refresh_token(
        {"sub": str(user_id), "sid": str(session_obj.id), "user_type": "student"}
    )
    new_access = create_access_token(
        {"sub": str(user_id), "sid": str(session_obj.id), "user_type": "student"}
    )

    session_obj.refresh_token = new_refresh
    db.add(session_obj)
    db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }
