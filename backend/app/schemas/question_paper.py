from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.question import QuestionInDB

class QuestionPaperBase(BaseModel):
    assessment_id: str
    version: str = "A"
    total_marks: int
    total_questions: int
    generated_for: Optional[str] = None
    questions: List[QuestionInDB]
    generation_metadata: Dict[str, Any] = {}

class QuestionPaperCreate(QuestionPaperBase):
    pass

class QuestionPaperUpdate(BaseModel):
    version: Optional[str] = None

class QuestionPaperInDB(QuestionPaperBase):
    id: str
    created_at: datetime
    updated_at: datetime
