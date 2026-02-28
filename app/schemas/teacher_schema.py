# schemas/teacher_schema.py
from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime


class TeacherCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Full name is required")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class TeacherLogin(BaseModel):
    email: EmailStr
    password: str
    device_id: str

    @field_validator("password")
    def password_required(cls, v):
        if not v.strip():
            raise ValueError("Password is required")
        return v


class TeacherResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr

    created_at: datetime

    class Config:
        from_attributes = True


class TeacherAuthResponse(BaseModel):
    user: TeacherResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
