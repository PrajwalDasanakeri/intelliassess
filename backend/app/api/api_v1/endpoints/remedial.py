from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List
from app.schemas.performance import RemedialTestInDB, RemedialTestCreate
from app.services.remedial_service import remedial_service
from app.crud.crud_remedial import remedial_test as crud_remedial

router = APIRouter()

def get_current_student(x_student_id: str = Header(..., description="Student ID for mock auth")):
    if not x_student_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_student_id

@router.post("/generate", response_model=RemedialTestInDB, status_code=201)
async def generate_remedial_test(
    subject: str,
    student_id: str = Depends(get_current_student)
):
    try:
        return await remedial_service.generate_remedial_test(student_id=student_id, subject=subject)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my-tests", response_model=List[RemedialTestInDB])
async def get_my_remedial_tests(
    student_id: str = Depends(get_current_student)
):
    return await crud_remedial.get_multi(filters={"student_id": student_id})

@router.get("/{id}", response_model=RemedialTestInDB)
async def get_remedial_test(
    id: str,
    student_id: str = Depends(get_current_student)
):
    test = await crud_remedial.get(id=id)
    if not test or test.student_id != student_id:
        raise HTTPException(status_code=404, detail="Remedial test not found")
    return test
