from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate, AssessmentInDB
from app.crud.crud_assessment import assessment as crud_assessment

router = APIRouter()

@router.post("/", response_model=AssessmentInDB, status_code=201)
async def create_assessment(assessment_in: AssessmentCreate):
    return await crud_assessment.create(obj_in=assessment_in)

@router.get("/{id}", response_model=AssessmentInDB)
async def get_assessment(id: str):
    a = await crud_assessment.get(id=id)
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return a

@router.get("/", response_model=List[AssessmentInDB])
async def list_assessments(skip: int = 0, limit: int = 100):
    return await crud_assessment.get_multi(skip=skip, limit=limit)

@router.put("/{id}", response_model=AssessmentInDB)
async def update_assessment(id: str, assessment_in: AssessmentUpdate):
    a = await crud_assessment.update(id=id, obj_in=assessment_in)
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return a

@router.delete("/{id}", status_code=204)
async def delete_assessment(id: str):
    success = await crud_assessment.delete(id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Assessment not found")
