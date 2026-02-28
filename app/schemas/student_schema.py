# schemas/student_schema.py
from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime


class StudentCreate(BaseModel):
    full_name: str
    roll_no: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    def name_required(cls, v):
        if not v.strip():
            raise ValueError("Full name is required")
        return v

    @field_validator("roll_no")
    def roll_required(cls, v):
        if not isinstance(v, str):
            raise ValueError("Roll no must be string")
        if not v.strip():
            raise ValueError("Roll no is required")
        return v

    @field_validator("password")
    def password_required(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class StudentLogin(BaseModel):
    email: EmailStr
    password: str
    device_id: str  # required for session tracking

    @field_validator("password")
    def password_required(cls, v):
        if not v.strip():
            raise ValueError("Password is required")
        return v


class StudentResponse(BaseModel):
    id: UUID
    full_name: str
    roll_no: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class StudentAuthResponse(BaseModel):
    user: StudentResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
