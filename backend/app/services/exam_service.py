from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.crud.crud_exam import crud_exam
from app.crud.crud_assessment import assessment as crud_assessment
from app.crud.crud_question_paper import question_paper as crud_question_paper
from app.schemas.exam import ExamSessionCreate, ExamSessionUpdate, ExamStatus, ExamStartResponse, AnswerSubmission, StudentResponse

class ExamService:
    
    async def start_exam(self, assessment_id: str, student_id: str) -> ExamStartResponse:
        # Verify assessment exists
        assessment = await crud_assessment.get(id=assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
            
        # Verify existing active session
        existing_session = await crud_exam.get_active_session(student_id=student_id, assessment_id=assessment_id)
        if existing_session:
            return await self._get_exam_payload(existing_session, assessment)
            
        # Get a question paper for this assessment (e.g. latest or random)
        papers = await crud_question_paper.get_multi(filters={"assessment_id": assessment_id}, limit=1)
        if not papers:
            raise HTTPException(status_code=400, detail="No question paper generated for this assessment yet")
        paper = papers[0]
        
        now = datetime.now(timezone.utc)
        duration = timedelta(minutes=assessment.duration_minutes)
        end_time = now + duration
        
        # Create session
        session_create = ExamSessionCreate(
            student_id=student_id,
            assessment_id=assessment_id,
            question_paper_id=paper.id,
            status=ExamStatus.IN_PROGRESS,
            start_time=now,
            end_time=end_time
        )
        session = await crud_exam.create(session_create)
        
        return await self._get_exam_payload(session, assessment, paper)

    async def _get_exam_payload(self, session, assessment, paper=None) -> ExamStartResponse:
        if not paper:
            paper = await crud_question_paper.get(id=session.question_paper_id)
            
        # Strip answers and metadata
        safe_questions = []
        for q in paper.questions:
            q_dict = q.model_dump()
            q_dict.pop("correct_answer", None)
            q_dict.pop("rubric", None)
            q_dict.pop("validation_metadata", None)
            q_dict.pop("ai_metadata", None)
            safe_questions.append(q_dict)
            
        return ExamStartResponse(
            session_id=session.id,
            assessment_id=assessment.id,
            status=session.status,
            start_time=session.start_time,
            end_time=session.end_time,
            questions=safe_questions
        )

    async def submit_answers(self, session_id: str, student_id: str, answers: List[AnswerSubmission]):
        session = await crud_exam.get(id=session_id)
        if not session or session.student_id != student_id:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
            
        if session.status != ExamStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Exam is not in progress")
            
        now = datetime.now(timezone.utc)
        if session.end_time:
            end_time = session.end_time.replace(tzinfo=timezone.utc) if session.end_time.tzinfo is None else session.end_time
            if now > end_time:
                # Time expired, auto-submit what we had
                await self._finalize_exam(session, now)
                raise HTTPException(status_code=400, detail="Exam time has expired")
            
        # Merge answers
        existing_responses = {r.question_id: r for r in session.responses}
        for a in answers:
            existing_responses[a.question_id] = StudentResponse(
                question_id=a.question_id,
                student_answer=a.student_answer,
                timestamp=now
            )
            
        await crud_exam.update_responses(id=session.id, responses=list(existing_responses.values()))
        return {"status": "success"}

    async def complete_exam(self, session_id: str, student_id: str):
        session = await crud_exam.get(id=session_id)
        if not session or session.student_id != student_id:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
            
        if session.status != ExamStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Exam is not in progress")
            
        now = datetime.now(timezone.utc)
        await self._finalize_exam(session, now)
        return {"status": "success"}

    async def _finalize_exam(self, session, submit_time: datetime):
        update = ExamSessionUpdate(
            status=ExamStatus.COMPLETED,
            submission_time=submit_time
        )
        await crud_exam.update(id=session.id, obj_in=update)

exam_service = ExamService()
