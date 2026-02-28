from fastapi import APIRouter
from app.api.v1.endpoints.auth.teacher_auth_router import router as teacher_auth_router
from app.api.v1.endpoints.auth.student_auth_router import router as student_auth_router
from app.api.v1.endpoints.room.room_teacher_router import router as room_teacher_router
from app.api.v1.endpoints.room.room_student_router import router as room_student_router


api_router = APIRouter(prefix="/api/v1")



api_router.include_router(teacher_auth_router)
api_router.include_router(student_auth_router)
api_router.include_router(room_student_router)
api_router.include_router(room_teacher_router)