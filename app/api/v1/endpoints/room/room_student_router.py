# app/api/v1/endpoints/room/room_student_router.py
import random
import string
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.room_models import Room
from app.models.student_models import Student
from app.models.attendance_token_models import AttendanceToken
from app.schemas.room_schema import RoomResponse
from app.schemas.join_schema import JoinRoomRequest, JoinRoomResponse
from app.services.dependencies import get_current_student


router = APIRouter(prefix="/room", tags=["Room - Student"])


def generate_token(length: int = 10) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ==================================
# 📚 GET ALL JOINED ROOMS
# ==================================
@router.get("/student/all", response_model=List[RoomResponse])
def get_student_rooms(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    # 1️⃣ Find all tokens assigned to this student
    tokens = (
        db.query(AttendanceToken)
        .filter(
            AttendanceToken.assigned_student_id == student.id,
            AttendanceToken.used == True,
        )
        .all()
    )

    if not tokens:
        raise HTTPException(status_code=404, detail="Student has not joined any rooms")

    # 2️⃣ Extract room_ids
    room_ids = [token.room_id for token in tokens]

    # 3️⃣ Fetch rooms
    rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()

    return rooms


# ==================================
# 🚀 JOIN ROOM
# ==================================
@router.post("/join", response_model=JoinRoomResponse)
def join_room(
    payload: JoinRoomRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    # 1️⃣ Find room
    room = db.query(Room).filter(Room.room_code == payload.room_code.upper()).first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Normalize roll to the same width used during token generation
    roll_width = max(len(str(room.starting_roll)), len(str(room.ending_roll)))
    student_roll = str(student.roll_no)
    normalized_roll = (
        student_roll.zfill(roll_width) if student_roll.isdigit() else student_roll
    )

    # 2️⃣ Find token using student's roll
    token_entry = (
        db.query(AttendanceToken)
        .filter(
            AttendanceToken.room_id == room.id,
            AttendanceToken.roll_no == normalized_roll,
        )
        .with_for_update()
        .first()
    )

    if not token_entry:
        raise HTTPException(
            status_code=404, detail="Your roll number is not valid for this room"
        )

    if token_entry.used:
        raise HTTPException(
            status_code=400,
            detail="Attendance token already used. Ask your teacher to issue a new attendance token.",
        )

    # 3️⃣ Assign token (first join only)
    token_entry.used = True
    token_entry.assigned_student_id = student.id

    # Attendance token is also a one-time voucher: return it once, then remove it from the cloud.
    issued_attendance_token = token_entry.token
    for _ in range(10):
        rotated = generate_token()
        exists = (
            db.query(AttendanceToken).filter(AttendanceToken.token == rotated).first()
        )
        if not exists:
            token_entry.token = rotated
            break
    else:
        raise HTTPException(
            status_code=500,
            detail="Could not rotate attendance token. Please try again.",
        )

    # Fingerprint token is a one-time voucher: return it once, then delete it.
    fingerprint_token = token_entry.fingerprint_token
    if fingerprint_token is not None:
        token_entry.fingerprint_token = None

    db.commit()

    return JoinRoomResponse(
        room_id=room.id,
        room_code=room.room_code,
        room_name=room.room_name,
        roll_no=normalized_roll,
        token=issued_attendance_token,
        fingerprint_token=fingerprint_token,
    )
