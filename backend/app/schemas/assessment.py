from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from app.schemas.enums import QuestionType, DifficultyLevel

class AssessmentBlueprint(BaseModel):
    total_questions: int
    difficulty_distribution: Dict[str, int]  # e.g., {"easy": 30, "medium": 50, "hard": 20} (percentages)
    type_distribution: Dict[str, int]        # e.g., {"mcq": 50, "short_answer": 50} (percentages)
    topic_distribution: Optional[Dict[str, int]] = None
    blooms_taxonomy_distribution: Optional[Dict[str, int]] = None
    marks_distribution: Optional[Dict[str, int]] = None
    topics: List[str]

class AssessmentBase(BaseModel):
    title: str
    description: str
    subject: str
    class_level: str
    blueprint: AssessmentBlueprint
    duration_minutes: int
    total_marks: int
    question_ids: List[str] = []

class AssessmentCreate(AssessmentBase):
    pass

class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None
    question_ids: Optional[List[str]] = None

class AssessmentInDB(AssessmentBase):
    id: str
    created_at: datetime
    updated_at: datetime
