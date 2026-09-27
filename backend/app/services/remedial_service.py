import uuid
from typing import List, Dict, Any
from datetime import datetime
from app.crud.crud_performance import performance_profile as crud_performance
from app.crud.crud_remedial import remedial_test as crud_remedial
from app.crud.crud_assessment import assessment as crud_assessment
from app.schemas.performance import RemedialTestCreate
from app.schemas.assessment import AssessmentCreate, AssessmentBlueprint

class RemedialService:
    async def generate_remedial_test(self, student_id: str, subject: str) -> RemedialTestCreate:
        profile = await crud_performance.get_by_student_and_subject(student_id, subject)
        if not profile:
            raise ValueError("No performance profile found for this student and subject.")
            
        weak_topics = profile.weak_topics
        if not weak_topics:
            raise ValueError("No weak topics identified for this student. No remedial test needed.")
            
        # Determine adaptive difficulty
        # Since the student is weak in these topics, we should target easy/medium questions
        selected_difficulty = "easy"
        
        # Create a new assessment specifically for this remedial test
        assessment_data = AssessmentCreate(
            title=f"Remedial Test - {subject} - {datetime.now().strftime('%Y%m%d')}",
            description=f"Targeted assessment for weak topics: {', '.join(weak_topics)}",
            subject=subject,
            class_level=profile.class_level,
            duration_minutes=30,
            total_marks=len(weak_topics) * 5,
            blueprint=AssessmentBlueprint(
                total_questions=len(weak_topics) * 2, # 2 questions per weak topic
                difficulty_distribution={"easy": 70, "medium": 30},
                type_distribution={"mcq": 50, "short_answer": 50},
                topics=weak_topics
            )
        )
        
        assessment = await crud_assessment.create(obj_in=assessment_data)
        
        # Snapshot current performance for these topics
        snapshot = {topic: profile.topic_performance[topic].percentage for topic in weak_topics if topic in profile.topic_performance}
        
        remedial = await crud_remedial.create(
            obj_in=RemedialTestCreate(
                student_id=student_id,
                subject=subject,
                class_level=profile.class_level,
                assessment_id=assessment.id,
                weak_topics_targeted=weak_topics,
                selected_difficulty=selected_difficulty,
                performance_snapshot_before=snapshot
            )
        )
        
        return remedial

remedial_service = RemedialService()
