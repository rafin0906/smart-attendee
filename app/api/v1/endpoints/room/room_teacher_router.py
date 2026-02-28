# app/api/v1/endpoints/room/room_teacher_router.py
import random
import string
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.room_models import Room
from app.models.attendance_token_models import AttendanceToken
from app.models.teacher_models import Teacher
from app.schemas.room_schema import (
    AttendanceTokenSyncItem,
    ProvideFingerprintTokenRequest,
    ProvideFingerprintTokenResponse,
    RoomCreate,
    RoomResponse,
)
from app.services.dependencies import get_current_teacher
from fastapi import HTTPException, status
from app.schemas.room_schema import ProvideTokenRequest, ProvideTokenResponse


router = APIRouter(prefix="/room", tags=["Room - Teacher"])


# 🔐 Generate uppercase room code (6 chars)
def generate_room_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# 🔐 Generate token for each roll
def generate_token(length: int = 10) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ==============================
# 🚀 CREATE ROOM (Teacher Only)
# ==============================
@router.post("/create", response_model=RoomResponse)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    start = int(payload.starting_roll)
    end = int(payload.ending_roll)

    roll_width = max(len(str(payload.starting_roll)), len(str(payload.ending_roll)))

    capacity = end - start + 1

    # 🔥 Ensure unique room_code
    while True:
        room_code = generate_room_code()
        existing = db.query(Room).filter(Room.room_code == room_code).first()
        if not existing:
            break

    new_room = Room(
        room_code=room_code,
        room_name=payload.room_name,
        teacher_id=teacher.id,
        starting_roll=payload.starting_roll,
        ending_roll=payload.ending_roll,
        capacity=capacity,
    )

    db.add(new_room)
    db.flush()  # get ID before commit

    # 🔥 Pre-generate tokens for each roll
    for roll in range(start, end + 1):
        attendance_token = AttendanceToken(
            room_id=new_room.id,
            roll_no=str(roll).zfill(roll_width),
            token=generate_token(),
            fingerprint_token=generate_token(),
        )
        db.add(attendance_token)

    db.commit()
    db.refresh(new_room)

    return new_room


# ===================================
# 📚 GET ALL ROOMS CREATED BY TEACHER
# ===================================
@router.get("/teacher/all", response_model=List[RoomResponse])
def get_teacher_rooms(
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    rooms = (
        db.query(Room)
        .filter(Room.teacher_id == teacher.id)
        .order_by(Room.created_at.desc())
        .all()
    )

    return rooms


# ===================================
# 🔄 PROVIDE NEW TOKEN (Teacher Only)
# ===================================
@router.post("/provide-token", response_model=ProvideTokenResponse)
def provide_token(
    payload: ProvideTokenRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    # 1️⃣ Find room
    room = db.query(Room).filter(Room.room_code == payload.room_code).first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2️⃣ Ensure teacher owns this room
    if room.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this room"
        )

    # Normalize roll to the same width used during token generation
    roll_width = max(len(str(room.starting_roll)), len(str(room.ending_roll)))
    roll_no = payload.roll_no
    normalized_roll = roll_no.zfill(roll_width) if roll_no.isdigit() else roll_no

    # 3️⃣ Find attendance token
    token_entry = (
        db.query(AttendanceToken)
        .filter(
            AttendanceToken.room_id == room.id,
            AttendanceToken.roll_no == normalized_roll,
        )
        .first()
    )

    if not token_entry:
        raise HTTPException(
            status_code=404, detail="Roll number not found in this room"
        )

    # 4️⃣ Reset token state
    token_entry.used = False
    token_entry.assigned_student_id = None

    # 5️⃣ Generate new token
    token_entry.token = generate_token()

    db.commit()

    return ProvideTokenResponse(
        room_code=room.room_code,
        roll_no=normalized_roll,
        token=token_entry.token,
        fingerprint_token=None,
    )


# ===================================
# 🔄 PROVIDE FINGERPRINT TOKEN (Teacher Only)
# ===================================
@router.post(
    "/provide-fingerprint-token",
    response_model=ProvideFingerprintTokenResponse,
)
def provide_fingerprint_token(
    payload: ProvideFingerprintTokenRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    room = db.query(Room).filter(Room.room_code == payload.room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this room",
        )

    roll_width = max(len(str(room.starting_roll)), len(str(room.ending_roll)))
    roll_no = payload.roll_no
    normalized_roll = roll_no.zfill(roll_width) if roll_no.isdigit() else roll_no

    token_entry = (
        db.query(AttendanceToken)
        .filter(
            AttendanceToken.room_id == room.id,
            AttendanceToken.roll_no == normalized_roll,
        )
        .first()
    )

    if not token_entry:
        raise HTTPException(
            status_code=404, detail="Roll number not found in this room"
        )

    token_entry.fingerprint_token = generate_token()
    db.commit()

    return ProvideFingerprintTokenResponse(
        room_code=room.room_code,
        roll_no=normalized_roll,
        fingerprint_token=token_entry.fingerprint_token,
    )


# ===================================
# 🔁 SYNC TOKENS (Teacher Only)
# ===================================
@router.get("/sync-tokens/{room_code}", response_model=List[AttendanceTokenSyncItem])
def sync_tokens(
    room_code: str,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    room = db.query(Room).filter(Room.room_code == room_code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this room",
        )

    tokens = db.query(AttendanceToken).filter(AttendanceToken.room_id == room.id).all()
    return tokens
