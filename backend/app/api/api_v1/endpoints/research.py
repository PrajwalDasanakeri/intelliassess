from fastapi import APIRouter, Depends, HTTPException, Header
from app.services.analytics_service import analytics_service
from app.schemas.analytics import ResearchMetricCreate
from app.crud.crud_analytics import research_metric as crud_analytics
from typing import List

router = APIRouter()

def get_current_teacher(x_teacher_id: str = Header(..., description="Teacher ID for mock auth")):
    if not x_teacher_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_teacher_id

@router.post("/calculate/{assessment_id}", response_model=List[ResearchMetricCreate])
async def calculate_research_metrics(assessment_id: str, current_teacher: str = Depends(get_current_teacher)):
    """
    Calculate and persist research metrics for a specific assessment.
    """
    metrics = []
    
    # Uniqueness
    u_metric = await analytics_service.calculate_question_uniqueness(assessment_id)
    if u_metric:
        metrics.append(u_metric)
        await crud_analytics.create(u_metric)
        
    # Syllabus Alignment
    sa_metric = await analytics_service.calculate_syllabus_alignment(assessment_id)
    if sa_metric:
        metrics.append(sa_metric)
        await crud_analytics.create(sa_metric)
        
    # Difficulty Consistency
    dc_metric = await analytics_service.calculate_difficulty_consistency(assessment_id)
    if dc_metric:
        metrics.append(dc_metric)
        await crud_analytics.create(dc_metric)
        
    # Evaluation Accuracy
    ea_metric = await analytics_service.calculate_evaluation_accuracy()
    metrics.append(ea_metric)
    await crud_analytics.create(ea_metric)
    
    # Weak Topic Identification
    wt_metric = await analytics_service.calculate_weak_topic_identification_metric()
    metrics.append(wt_metric)
    await crud_analytics.create(wt_metric)
    
    # Student Improvement
    si_metric = await analytics_service.calculate_student_improvement()
    metrics.append(si_metric)
    await crud_analytics.create(si_metric)
    
    return metrics

@router.get("/metrics", response_model=List[ResearchMetricCreate])
async def get_research_metrics(current_teacher: str = Depends(get_current_teacher), skip: int = 0, limit: int = 100):
    """
    Retrieve stored research metrics.
    """
    metrics = await crud_analytics.get_multi(skip=skip, limit=limit)
    return metrics
