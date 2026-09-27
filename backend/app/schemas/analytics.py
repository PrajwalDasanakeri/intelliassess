from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class ResearchMetricBase(BaseModel):
    metric_name: str
    metric_type: str # e.g., 'uniqueness', 'alignment', 'consistency', 'accuracy', 'improvement', 'intervention'
    value: Optional[float] = None
    unit: Optional[str] = None # e.g., '%', 'absolute', 'count'
    assessment_id: Optional[str] = None
    subject: Optional[str] = None
    student_id: Optional[str] = None
    sample_size: int = 0
    calculation_method: str
    limitations: Optional[str] = None
    status: str = "calculated" # 'calculated', 'insufficient_data'

class ResearchMetricCreate(ResearchMetricBase):
    pass

class ResearchMetricInDB(ResearchMetricBase):
    id: str = Field(alias="id")
    calculation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OverviewStats(BaseModel):
    total_assessments: int = 0
    total_questions: int = 0
    total_attempts: int = 0
    average_score_percentage: float = 0.0

class TopicStats(BaseModel):
    topic: str
    total_attempts: int = 0
    average_percentage: float = 0.0
    weak_count: int = 0
    strong_count: int = 0

class SubjectPerformance(BaseModel):
    subject: str
    overall_percentage: float = 0.0
    total_students: int = 0
    topic_distribution: List[TopicStats] = Field(default_factory=list)

class RemedialStats(BaseModel):
    total_generated: int = 0
    total_completed: int = 0
    average_improvement_percentage: Optional[float] = None
    
class TeacherDashboardAnalytics(BaseModel):
    overview: OverviewStats
    performance_by_subject: List[SubjectPerformance]
    remedial_learning: RemedialStats
    
class StudentDashboardAnalytics(BaseModel):
    student_id: str
    overall_percentage: float = 0.0
    subject_performance: List[SubjectPerformance]
    remedial_learning: RemedialStats
