from typing import List, Dict, Any, Tuple
from app.crud.crud_evaluation import evaluation as crud_evaluation
from app.crud.crud_question import question as crud_question
from app.crud.crud_exam import crud_exam
from app.crud.crud_performance import performance_profile as crud_performance
from app.crud.crud_remedial import remedial_test as crud_remedial
from app.crud.crud_assessment import assessment as crud_assessment
from app.schemas.performance import (
    PerformanceProfileCreate, PerformanceProfileUpdate,
    TopicPerformance, RemedialTestCreate, RemedialTestUpdate, RemedialTestStatus
)
from app.core.config import settings

class PerformanceService:
    async def analyze_exam_and_update_profile(self, exam_session_id: str) -> None:
        """
        Analyzes a graded exam session and updates the student's performance profile.
        Also tracks if this was a remedial test to calculate improvement.
        """
        exam = await crud_exam.get(id=exam_session_id)
        if not exam:
            raise ValueError("Exam not found")
            
        evaluations = await crud_evaluation.get_by_exam_session(exam_session_id)
        if not evaluations:
            return # Nothing to analyze
            
        student_id = exam.student_id
        assessment = await crud_assessment.get(id=exam.assessment_id)
        if not assessment:
            return
            
        subject = assessment.subject
        class_level = assessment.class_level
        
        # Get existing profile
        profile = await crud_performance.get_by_student_and_subject(student_id, subject)
        
        if not profile:
            profile = await crud_performance.create(obj_in=PerformanceProfileCreate(
                student_id=student_id,
                subject=subject,
                class_level=class_level
            ))

        # Aggregate new topic performances
        topic_updates: Dict[str, TopicPerformance] = {}
        for ev in evaluations:
            q = await crud_question.get(id=ev.question_id)
            if not q:
                continue
            topic = q.topic
            
            if topic not in topic_updates:
                if topic in profile.topic_performance:
                    # Deep copy existing to update
                    topic_updates[topic] = TopicPerformance(**profile.topic_performance[topic].model_dump())
                else:
                    topic_updates[topic] = TopicPerformance(topic=topic)
            
            t = topic_updates[topic]
            t.total_questions += 1
            t.attempted_questions += 1 if ev.awarded_marks is not None else 0
            t.obtained_marks += ev.awarded_marks
            t.maximum_marks += ev.maximum_marks
            if t.maximum_marks > 0:
                t.percentage = t.obtained_marks / t.maximum_marks
                
            if t.percentage >= settings.STRONG_TOPIC_THRESHOLD:
                t.classification = "strong"
            elif t.percentage < settings.WEAK_TOPIC_THRESHOLD:
                t.classification = "weak"
            else:
                t.classification = "average"

        # Merge topic updates into profile
        new_topic_performance = profile.topic_performance.copy()
        for topic, tp in topic_updates.items():
            new_topic_performance[topic] = tp
            
        # Re-calculate overall
        total_q = sum(t.total_questions for t in new_topic_performance.values())
        total_obtained = sum(t.obtained_marks for t in new_topic_performance.values())
        total_max = sum(t.maximum_marks for t in new_topic_performance.values())
        overall_perc = total_obtained / total_max if total_max > 0 else 0.0
        
        weak_topics = [t.topic for t in new_topic_performance.values() if t.classification == "weak"]
        strong_topics = [t.topic for t in new_topic_performance.values() if t.classification == "strong"]
        
        history = profile.assessment_history
        if exam_session_id not in history:
            history.append(exam_session_id)

        update_data = PerformanceProfileUpdate(
            total_questions_encountered=total_q,
            total_marks_obtained=total_obtained,
            total_maximum_marks=total_max,
            overall_percentage=overall_perc,
            topic_performance=new_topic_performance,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            assessment_history=history
        )
        
        updated_profile = await crud_performance.update(db_obj=profile, obj_in=update_data)
        
        # Check if this was a remedial test and calculate improvement
        remedial_tests = await crud_remedial.get_multi(filters={"exam_session_id": exam_session_id})
        if remedial_tests:
            remedial = remedial_tests[0]
            # Calculate improvement
            improvement = {}
            for wt in remedial.weak_topics_targeted:
                before_perc = remedial.performance_snapshot_before.get(wt, 0)
                after_perc = updated_profile.topic_performance[wt].percentage if wt in updated_profile.topic_performance else 0
                improvement[wt] = after_perc - before_perc
                
            await crud_remedial.update(
                db_obj=remedial,
                obj_in=RemedialTestUpdate(
                    status=RemedialTestStatus.COMPLETED,
                    performance_snapshot_after={wt: updated_profile.topic_performance[wt].percentage for wt in remedial.weak_topics_targeted if wt in updated_profile.topic_performance},
                    improvement_metrics=improvement
                )
            )

    async def get_student_performance(self, student_id: str, subject: Optional[str] = None) -> List[Any]:
        filters = {"student_id": student_id}
        if subject:
            filters["subject"] = subject
        return await crud_performance.get_multi(filters=filters)

performance_service = PerformanceService()
