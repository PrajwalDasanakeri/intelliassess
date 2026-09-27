from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from app.schemas.enums import QuestionType, DifficultyLevel, BloomsTaxonomy, QuestionStatus, SourceType

class Option(BaseModel):
    id: str
    text: str
    is_correct: bool

class QuestionBase(BaseModel):
    text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    blooms_taxonomy: BloomsTaxonomy
    subject: str
    topic: str
    class_level: str
    marks: int = 1
    options: Optional[List[Option]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    status: QuestionStatus = QuestionStatus.DRAFT
    source: SourceType = SourceType.MANUAL

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    difficulty: Optional[DifficultyLevel] = None
    blooms_taxonomy: Optional[BloomsTaxonomy] = None
    options: Optional[List[Option]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    status: Optional[QuestionStatus] = None

class QuestionInDB(QuestionBase):
    id: str
    created_at: datetime
    updated_at: datetime
