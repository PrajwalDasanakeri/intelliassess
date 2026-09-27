from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ExamStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    GRADED = "graded"

class StudentResponse(BaseModel):
    question_id: str
    student_answer: Any  # Could be string, list of strings, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExamSessionBase(BaseModel):
    student_id: str
    assessment_id: str
    question_paper_id: Optional[str] = None
    status: ExamStatus = ExamStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    submission_time: Optional[datetime] = None

class ExamSessionCreate(ExamSessionBase):
    pass

class ExamSessionUpdate(BaseModel):
    status: Optional[ExamStatus] = None
    question_paper_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    submission_time: Optional[datetime] = None

class ExamSessionInDB(ExamSessionBase):
    id: str = Field(alias="id")
    responses: List[StudentResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

class ExamStartResponse(BaseModel):
    session_id: str
    assessment_id: str
    status: ExamStatus
    start_time: datetime
    end_time: datetime
    questions: List[Dict[str, Any]] # Strip out correct answers

class AnswerSubmission(BaseModel):
    question_id: str
    student_answer: Any

