# schemas/join_schema.py
from pydantic import BaseModel, field_validator
from uuid import UUID


class JoinRoomRequest(BaseModel):
    room_code: str

    @field_validator("room_code")
    def validate_room_code(cls, v):
        if not v.strip():
            raise ValueError("Room code is required")
        if len(v) != 6:
            raise ValueError("Room code must be 6 characters")
        return v.upper()


class JoinRoomResponse(BaseModel):
    room_id: UUID
    room_code: str
    room_name: str
    roll_no: str
    token: str
    fingerprint_token: str | None = None
