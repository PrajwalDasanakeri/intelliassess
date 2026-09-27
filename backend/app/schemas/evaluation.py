from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone
from enum import Enum

class EvaluationMethod(str, Enum):
    OBJECTIVE = "objective"
    SEMANTIC = "semantic"
    LLM = "llm"

class EvaluationCriterion(BaseModel):
    criterion: str
    marks_awarded: float
    reason: str

class EvaluationBase(BaseModel):
    exam_session_id: str
    student_id: str
    question_id: str
    response_id: str
    awarded_marks: float
    maximum_marks: float
    ai_feedback: Optional[str] = None
    confidence_score: Optional[float] = None
    evaluation_method: EvaluationMethod
    human_override: bool = False
    human_marks: Optional[float] = None
    human_feedback: Optional[str] = None
    criteria: Optional[List[EvaluationCriterion]] = None

class EvaluationCreate(EvaluationBase):
    pass

class EvaluationUpdate(BaseModel):
    human_override: Optional[bool] = None
    human_marks: Optional[float] = None
    human_feedback: Optional[str] = None

class EvaluationInDB(EvaluationBase):
    id: str = Field(alias="id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LLMEvaluationResult(BaseModel):
    awarded_marks: float
    maximum_marks: float
    confidence_score: float
    feedback: str
    criteria: List[EvaluationCriterion] = []
    
    @model_validator(mode='before')
    @classmethod
    def check_marks(cls, values):
        awarded = values.get('awarded_marks', 0)
        max_marks = values.get('maximum_marks', 1)
        if awarded > max_marks:
            values['awarded_marks'] = max_marks # Clamp
        if awarded < 0:
            values['awarded_marks'] = 0 # Clamp
        return values
