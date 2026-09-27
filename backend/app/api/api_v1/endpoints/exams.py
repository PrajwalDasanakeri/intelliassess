from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from app.schemas.exam import ExamStartResponse, AnswerSubmission, ExamSessionInDB
from app.services.exam_service import exam_service
from app.crud.crud_exam import crud_exam

router = APIRouter()

def get_current_student(x_student_id: str = Header(..., description="Student ID for mock auth")):
    if not x_student_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_student_id

@router.post("/{assessment_id}/start", response_model=ExamStartResponse)
async def start_exam(
    assessment_id: str,
    student_id: str = Depends(get_current_student)
):
    return await exam_service.start_exam(assessment_id=assessment_id, student_id=student_id)

@router.get("/{session_id}", response_model=ExamSessionInDB)
async def get_exam_session(
    session_id: str,
    student_id: str = Depends(get_current_student)
):
    session = await crud_exam.get(id=session_id)
    if not session or session.student_id != student_id:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    return session

@router.post("/{session_id}/answers")
async def submit_answers(
    session_id: str,
    answers: List[AnswerSubmission],
    student_id: str = Depends(get_current_student)
):
    return await exam_service.submit_answers(session_id=session_id, student_id=student_id, answers=answers)

@router.post("/{session_id}/submit")
async def complete_exam(
    session_id: str,
    student_id: str = Depends(get_current_student)
):
    return await exam_service.complete_exam(session_id=session_id, student_id=student_id)

@router.get("/my/attempts", response_model=List[ExamSessionInDB])
async def get_my_attempts(
    student_id: str = Depends(get_current_student)
):
    return await crud_exam.get_multi(filters={"student_id": student_id})

from app.services.evaluation_service import AnswerEvaluationService
from app.api.api_v1.endpoints.questions import llm_client
from app.core.database import db
from app.crud.crud_evaluation import evaluation as crud_evaluation
from app.schemas.evaluation import EvaluationInDB

def get_evaluation_service():
    return AnswerEvaluationService(llm_client)

@router.post("/{session_id}/evaluate", response_model=List[EvaluationInDB])
async def evaluate_exam_session(
    session_id: str,
    eval_service: AnswerEvaluationService = Depends(get_evaluation_service),
    # Assuming any authorized user (teacher or system) can trigger this
):
    try:
        results = await eval_service.evaluate_exam(exam_session_id=session_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{session_id}/evaluation", response_model=List[EvaluationInDB])
async def get_exam_evaluation(
    session_id: str,
    student_id: str = Depends(get_current_student)
):
    # Verify the student owns this exam
    session = await crud_exam.get(id=session_id)
    if not session or session.student_id != student_id:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
        
    evals = await crud_evaluation.get_by_exam_session(session_id)
    return evals
