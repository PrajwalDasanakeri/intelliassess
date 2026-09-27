from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class TopicPerformance(BaseModel):
    topic: str
    total_questions: int = 0
    attempted_questions: int = 0
    correct_answers: int = 0
    obtained_marks: float = 0.0
    maximum_marks: float = 0.0
    percentage: float = 0.0
    classification: str = "average" # strong, average, weak

class PerformanceProfileBase(BaseModel):
    student_id: str
    subject: str
    class_level: str
    total_questions_encountered: int = 0
    total_marks_obtained: float = 0.0
    total_maximum_marks: float = 0.0
    overall_percentage: float = 0.0
    topic_performance: Dict[str, TopicPerformance] = Field(default_factory=dict)
    weak_topics: List[str] = Field(default_factory=list)
    strong_topics: List[str] = Field(default_factory=list)
    assessment_history: List[str] = Field(default_factory=list) # List of exam_session_ids
    
class PerformanceProfileCreate(PerformanceProfileBase):
    pass

class PerformanceProfileUpdate(BaseModel):
    total_questions_encountered: Optional[int] = None
    total_marks_obtained: Optional[float] = None
    total_maximum_marks: Optional[float] = None
    overall_percentage: Optional[float] = None
    topic_performance: Optional[Dict[str, TopicPerformance]] = None
    weak_topics: Optional[List[str]] = None
    strong_topics: Optional[List[str]] = None
    assessment_history: Optional[List[str]] = None

class PerformanceProfileInDB(PerformanceProfileBase):
    id: str = Field(alias="id")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RemedialTestStatus(str, Enum):
    GENERATED = "generated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class RemedialTestBase(BaseModel):
    student_id: str
    subject: str
    class_level: str
    source_exam_session_id: Optional[str] = None
    assessment_id: str # Link to the generated assessment blueprint
    question_paper_id: Optional[str] = None
    exam_session_id: Optional[str] = None # Link to the exam session once started
    weak_topics_targeted: List[str]
    selected_difficulty: str
    performance_snapshot_before: Dict[str, Any] = Field(default_factory=dict)
    performance_snapshot_after: Optional[Dict[str, Any]] = None
    improvement_metrics: Optional[Dict[str, Any]] = None
    status: RemedialTestStatus = RemedialTestStatus.GENERATED
    generation_reason: str = "Targeting identified weak topics"

class RemedialTestCreate(RemedialTestBase):
    pass

class RemedialTestUpdate(BaseModel):
    question_paper_id: Optional[str] = None
    exam_session_id: Optional[str] = None
    status: Optional[RemedialTestStatus] = None
    performance_snapshot_after: Optional[Dict[str, Any]] = None
    improvement_metrics: Optional[Dict[str, Any]] = None

class RemedialTestInDB(RemedialTestBase):
    id: str = Field(alias="id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

