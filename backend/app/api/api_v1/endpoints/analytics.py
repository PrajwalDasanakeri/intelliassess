from fastapi import APIRouter, Depends, HTTPException, Header
from app.services.analytics_service import analytics_service
from app.schemas.analytics import TeacherDashboardAnalytics, StudentDashboardAnalytics

router = APIRouter()

def get_current_teacher(x_teacher_id: str = Header(..., description="Teacher ID for mock auth")):
    if not x_teacher_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_teacher_id

def get_current_student(x_student_id: str = Header(..., description="Student ID for mock auth")):
    if not x_student_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_student_id

@router.get("/overview/teacher", response_model=TeacherDashboardAnalytics)
async def get_teacher_overview(current_teacher: str = Depends(get_current_teacher)):
    """
    Get overview statistics for the teacher/admin dashboard.
    """
    return await analytics_service.get_teacher_dashboard()

@router.get("/overview/student", response_model=StudentDashboardAnalytics)
async def get_student_overview(current_student: str = Depends(get_current_student)):
    """
    Get overview statistics for the authenticated student.
    """
    return await analytics_service.get_student_dashboard(current_student)
