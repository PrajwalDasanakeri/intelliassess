from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List
from app.schemas.performance import PerformanceProfileInDB
from app.services.performance_service import performance_service
from app.crud.crud_performance import performance_profile as crud_performance

router = APIRouter()

def get_current_student(x_student_id: str = Header(..., description="Student ID for mock auth")):
    if not x_student_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_student_id

@router.get("/my-profile", response_model=List[PerformanceProfileInDB])
async def get_my_performance(
    student_id: str = Depends(get_current_student),
    subject: str = None
):
    return await performance_service.get_student_performance(student_id=student_id, subject=subject)

@router.get("/weak-topics", response_model=List[str])
async def get_weak_topics(
    subject: str,
    student_id: str = Depends(get_current_student)
):
    profile = await crud_performance.get_by_student_and_subject(student_id, subject)
    if not profile:
        return []
    return profile.weak_topics
