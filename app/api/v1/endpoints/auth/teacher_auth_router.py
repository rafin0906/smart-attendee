#  app/api/v1/endpoints/auth/teacher_auth_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.teacher_models import Teacher
from app.models.session_models import Session as UserSession
from app.schemas.teacher_schema import (
    TeacherCreate,
    TeacherLogin,
    TeacherResponse,
    TeacherAuthResponse,
)

from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.jwt import SECRET_KEY, ALGORITHM
from jose import jwt
from pydantic import BaseModel

router = APIRouter(prefix="/teacher", tags=["Teacher Auth"])


@router.post("/sign_up", response_model=TeacherResponse)
def teacher_sign_up(payload: TeacherCreate, db: Session = Depends(get_db)):
    existing_teacher = db.query(Teacher).filter(Teacher.email == payload.email).first()

    if existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_teacher = Teacher(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )

    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    return new_teacher


@router.post("/sign_in", response_model=TeacherAuthResponse)
def teacher_sign_in(
    payload: TeacherLogin, db: Session = Depends(get_db)
) -> TeacherAuthResponse:
    teacher = db.query(Teacher).filter(Teacher.email == payload.email).first()

    if not teacher or not verify_password(payload.password, teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # 🔥 Single-device login: remove ALL previous sessions of this teacher
    db.query(UserSession).filter(UserSession.user_id == teacher.id).delete()
    db.commit()

    session_id = uuid.uuid4()
    refresh_token = create_refresh_token(
        {"sub": str(teacher.id), "sid": str(session_id), "user_type": "teacher"}
    )

    new_session = UserSession(
        id=session_id,
        user_id=teacher.id,
        device_id=payload.device_id,
        refresh_token=refresh_token,
    )

    db.add(new_session)
    db.commit()

    access_token = create_access_token(
        {"sub": str(teacher.id), "sid": str(session_id), "user_type": "teacher"}
    )

    return {
        "user": teacher,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


class RefreshTokenPayload(BaseModel):
    refresh_token: str


@router.post("/refresh")
def teacher_refresh_token(payload: RefreshTokenPayload, db: Session = Depends(get_db)):
    refresh_token = payload.refresh_token

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

    session_obj = (
        db.query(UserSession)
        .filter(UserSession.id == sid_uuid, UserSession.refresh_token == refresh_token)
        .first()
    )

    if not session_obj or str(session_obj.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session or token"
        )

    new_refresh = create_refresh_token(
        {"sub": str(user_id), "sid": str(session_obj.id), "user_type": "teacher"}
    )
    new_access = create_access_token(
        {"sub": str(user_id), "sid": str(session_obj.id), "user_type": "teacher"}
    )

    session_obj.refresh_token = new_refresh
    db.add(session_obj)
    db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }
