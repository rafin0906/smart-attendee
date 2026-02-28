# schemas/room_schema.py
from pydantic import BaseModel, field_validator

from uuid import UUID
from datetime import datetime
from typing import Any


class RoomCreate(BaseModel):
    room_name: str
    starting_roll: str
    ending_roll: str

    @field_validator("starting_roll")
    def validate_start_roll(cls, v):
        if not isinstance(v, str):
            raise ValueError("Starting roll must be string")
        if not v.strip():
            raise ValueError("Starting roll is required")
        return v

    @field_validator("ending_roll")
    def validate_end_roll(cls, v):
        if not isinstance(v, str):
            raise ValueError("Ending roll must be string")
        if not v.strip():
            raise ValueError("Ending roll is required")
        return v

    @field_validator("ending_roll")
    def check_roll_range(cls, v, info):
        start = info.data.get("starting_roll")
        if start and v.isdigit() and start.isdigit():
            if int(v) < int(start):
                raise ValueError("Ending roll must be greater than starting roll")
        return v

    @field_validator("room_name")
    def validate_room_name(cls, v):
        if not isinstance(v, str):
            raise ValueError("Room name must be string")
        if not v.strip():
            raise ValueError("Room name is required")
        return v


class RoomResponse(BaseModel):
    id: UUID
    room_code: str
    room_name: str
    starting_roll: str
    ending_roll: str
    capacity: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProvideTokenRequest(BaseModel):
    room_code: str
    roll_no: str

    @field_validator("room_code")
    def validate_room_code(cls, v):
        return v.upper()

    @field_validator("roll_no")
    def validate_roll(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Roll is required")
        if not v.isdigit():
            raise ValueError("Roll must contain only digits")
        return v


class ProvideTokenResponse(BaseModel):
    room_code: str
    roll_no: str
    token: str
    fingerprint_token: str | None = None


class ProvideFingerprintTokenRequest(BaseModel):
    room_code: str
    roll_no: str

    @field_validator("room_code")
    def validate_room_code(cls, v):
        return v.upper()

    @field_validator("roll_no")
    def validate_roll(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Roll is required")
        if not v.isdigit():
            raise ValueError("Roll must contain only digits")
        return v


class ProvideFingerprintTokenResponse(BaseModel):
    room_code: str
    roll_no: str
    fingerprint_token: str


class AttendanceTokenSyncItem(BaseModel):
    id: UUID
    room_id: UUID
    roll_no: str
    token: str
    fingerprint_token: str | None = None

    class Config:
        from_attributes = True
