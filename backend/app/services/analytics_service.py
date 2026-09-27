from typing import List, Dict, Any, Optional
from app.crud.crud_analytics import research_metric as crud_analytics
from app.crud.crud_assessment import assessment as crud_assessment
from app.crud.crud_question_paper import question_paper as crud_question_paper
from app.crud.crud_question import question as crud_question
from app.crud.crud_performance import performance_profile as crud_performance
from app.crud.crud_remedial import remedial_test as crud_remedial
from app.crud.crud_exam import crud_exam
from app.services.evaluation_service import SemanticSimilarityService
from app.schemas.analytics import (
    ResearchMetricCreate, TeacherDashboardAnalytics, OverviewStats, 
    SubjectPerformance, TopicStats, RemedialStats, StudentDashboardAnalytics
)

class AnalyticsService:

    async def calculate_difficulty_consistency(self, assessment_id: str) -> Optional[ResearchMetricCreate]:
        """
        Measures whether the generated question papers follow the requested difficulty distribution.
        Formula: MAE (Mean Absolute Error) between requested % and actual % across difficulty levels.
        """
        assessment = await crud_assessment.get(id=assessment_id)
        if not assessment:
            return None
            
        requested_dist = assessment.blueprint.difficulty_distribution # e.g. {'easy': 70, 'medium': 30}
        papers = await crud_question_paper.get_multi(filters={"assessment_id": assessment_id})
        
        if not papers:
            return ResearchMetricCreate(
                metric_name="Difficulty Consistency",
                metric_type="consistency",
                assessment_id=assessment_id,
                calculation_method="Mean Absolute Error (Requested vs Actual Difficulty)",
                status="insufficient_data",
                limitations="No question papers generated yet"
            )
            
        # Analyze the first generated paper as representative
        paper = papers[0]
        actual_counts = {"easy": 0, "medium": 0, "hard": 0}
        total_questions = 0
        
        for q in paper.questions:
            if q.difficulty in actual_counts:
                actual_counts[q.difficulty] += 1
                total_questions += 1
                
        if total_questions == 0:
            return None
            
        mae_sum = 0
        for diff, req_pct in requested_dist.items():
            actual_pct = (actual_counts[diff] / total_questions) * 100
            mae_sum += abs(req_pct - actual_pct)
            
        mae = mae_sum / len(requested_dist)
        
        # We can define consistency as 100 - MAE
        consistency_score = max(0, 100 - mae)
        
        return ResearchMetricCreate(
            metric_name="Difficulty Consistency",
            metric_type="consistency",
            value=consistency_score,
            unit="%",
            assessment_id=assessment_id,
            sample_size=total_questions,
            calculation_method="100 - Mean Absolute Error between requested and actual difficulty percentages",
            status="calculated"
        )

    async def calculate_syllabus_alignment(self, assessment_id: str) -> Optional[ResearchMetricCreate]:
        """
        Measures whether the generated questions are aligned with the requested topics in the blueprint.
        Formula: (Questions with topic in requested topics) / Total Questions * 100
        """
        assessment = await crud_assessment.get(id=assessment_id)
        if not assessment:
            return None
            
        requested_topics = set(assessment.blueprint.topics)
        papers = await crud_question_paper.get_multi(filters={"assessment_id": assessment_id})
        
        if not papers:
            return ResearchMetricCreate(
                metric_name="Topic Alignment",
                metric_type="alignment",
                assessment_id=assessment_id,
                calculation_method="Percentage of generated questions matching requested topics",
                status="insufficient_data",
                limitations="No question papers generated yet"
            )
            
        paper = papers[0]
        aligned_count = 0
        total_questions = 0
        
        for q in paper.questions:
            total_questions += 1
            if q.topic in requested_topics:
                aligned_count += 1
                    
        alignment_score = (aligned_count / total_questions * 100) if total_questions > 0 else 0
        
        return ResearchMetricCreate(
            metric_name="Topic Alignment",
            metric_type="alignment",
            value=alignment_score,
            unit="%",
            assessment_id=assessment_id,
            sample_size=total_questions,
            calculation_method="Percentage of generated questions whose topic is in the requested topics list",
            limitations="True syllabus alignment requires learning-objective metadata which is not available in the current data model. This metric only measures broad topic-level matching.",
            status="calculated"
        )

    async def calculate_evaluation_accuracy(self) -> ResearchMetricCreate:
        """
        Calculates accuracy between AI awarded marks and human reference marks.
        If no human reference marks exist in the system, returns insufficient_data.
        Note: Currently, the schema does not store 'human_awarded_marks', so we safely report missing data.
        """
        return ResearchMetricCreate(
            metric_name="Evaluation Accuracy",
            metric_type="accuracy",
            calculation_method="Mean Absolute Error between AI marks and Human Reference marks",
            status="insufficient_data",
            limitations="Human reference data unavailable"
        )

    async def calculate_student_improvement(self, student_id: str = None) -> ResearchMetricCreate:
        """
        Calculates average improvement across all completed remedial tests.
        """
        filters = {"status": "completed"}
        if student_id:
            filters["student_id"] = student_id
            
        remedials = await crud_remedial.get_multi(filters=filters)
        
        if not remedials:
            return ResearchMetricCreate(
                metric_name="Student Improvement",
                metric_type="improvement",
                student_id=student_id,
                calculation_method="Average of (After Percentage - Before Percentage) across completed remedial tests",
                status="insufficient_data",
                limitations="No completed remedial tests available"
            )
            
        total_improvement = 0.0
        topic_count = 0
        
        for r in remedials:
            if r.improvement_metrics:
                for imp in r.improvement_metrics.values():
                    total_improvement += imp
                    topic_count += 1
                    
        avg_improvement = (total_improvement / topic_count * 100) if topic_count > 0 else 0.0
        
        return ResearchMetricCreate(
            metric_name="Student Improvement",
            metric_type="improvement",
            student_id=student_id,
            value=avg_improvement,
            unit="% absolute",
            sample_size=topic_count, # number of topics intervened
            calculation_method="Average absolute percentage improvement (After % - Before %) across all targeted topics",
            status="calculated"
        )

    async def calculate_question_uniqueness(self, assessment_id: str) -> Optional[ResearchMetricCreate]:
        """
        Calculates uniqueness by comparing pairwise semantic similarity of generated question text 
        using Sentence-Transformers embeddings.
        """
        papers = await crud_question_paper.get_multi(filters={"assessment_id": assessment_id})
        if not papers:
            return ResearchMetricCreate(
                metric_name="Question Uniqueness",
                metric_type="uniqueness",
                assessment_id=assessment_id,
                calculation_method="Semantic similarity using SentenceTransformer",
                status="insufficient_data",
                limitations="No question papers generated"
            )
            
        paper = papers[0]
        q_texts = []
        for q in paper.questions:
            q_texts.append(q.text)
                
        if len(q_texts) < 2:
            return ResearchMetricCreate(
                metric_name="Question Uniqueness",
                metric_type="uniqueness",
                assessment_id=assessment_id,
                value=100.0,
                unit="%",
                sample_size=len(q_texts),
                calculation_method="Single question (100% unique by default)",
                status="calculated"
            )
            
        # Calculate semantic similarity across all pairs
        similarity_threshold = 0.85
        duplicate_pairs = 0
        total_pairs = 0
        
        for i in range(len(q_texts)):
            for j in range(i+1, len(q_texts)):
                sim = SemanticSimilarityService.calculate_similarity(q_texts[i], q_texts[j])
                if sim > similarity_threshold:
                    duplicate_pairs += 1
                total_pairs += 1
                
        uniqueness = (1.0 - (duplicate_pairs / total_pairs)) * 100
        
        return ResearchMetricCreate(
            metric_name="Question Uniqueness",
            metric_type="uniqueness",
            value=uniqueness,
            unit="%",
            assessment_id=assessment_id,
            sample_size=len(q_texts),
            calculation_method=f"100% - (Percentage of pairs exceeding semantic similarity threshold {similarity_threshold} using all-MiniLM-L6-v2)",
            status="calculated"
        )
        
    async def calculate_weak_topic_identification_metric(self) -> ResearchMetricCreate:
        """
        Measures how many topics are classified as weak vs total topics across all profiles.
        """
        profiles = await crud_performance.get_multi(limit=1000)
        
        total_topics_analyzed = 0
        weak_topics_identified = 0
        
        for p in profiles:
            total_topics_analyzed += len(p.topic_performance)
            weak_topics_identified += len(p.weak_topics)
            
        if total_topics_analyzed == 0:
            return ResearchMetricCreate(
                metric_name="Weak Topic Identification",
                metric_type="intervention",
                calculation_method="Count of weak topics / Total topics assessed",
                status="insufficient_data",
                limitations="No performance profiles available"
            )
            
        percentage = (weak_topics_identified / total_topics_analyzed) * 100
        
        return ResearchMetricCreate(
            metric_name="Weak Topic Identification",
            metric_type="intervention",
            value=percentage,
            unit="% of topics identified as weak",
            sample_size=total_topics_analyzed,
            calculation_method="Percentage of total assessed topics that fell below the weak threshold",
            status="calculated"
        )

    async def get_teacher_dashboard(self) -> TeacherDashboardAnalytics:
        assessments = await crud_assessment.get_multi(limit=1000)
        exams = await crud_exam.get_multi(limit=10000)
        profiles = await crud_performance.get_multi(limit=1000)
        remedials = await crud_remedial.get_multi(limit=1000)
        
        total_questions = sum(len(a.question_ids) for a in assessments)
        
        # Aggregate performance by subject
        subject_data: Dict[str, SubjectPerformance] = {}
        for p in profiles:
            if p.subject not in subject_data:
                subject_data[p.subject] = SubjectPerformance(subject=p.subject)
            
            sub = subject_data[p.subject]
            sub.total_students += 1
            # We will average the overall_percentage later
            sub.overall_percentage += p.overall_percentage
            
            for t_name, t_perf in p.topic_performance.items():
                # Find topic in sub
                t_stat = next((ts for ts in sub.topic_distribution if ts.topic == t_name), None)
                if not t_stat:
                    t_stat = TopicStats(topic=t_name)
                    sub.topic_distribution.append(t_stat)
                
                t_stat.total_attempts += 1
                t_stat.average_percentage += t_perf.percentage
                if t_perf.classification == "weak":
                    t_stat.weak_count += 1
                elif t_perf.classification == "strong":
                    t_stat.strong_count += 1
                    
        # Finalize averages
        overall_perc_sum = 0
        for sub in subject_data.values():
            if sub.total_students > 0:
                sub.overall_percentage = sub.overall_percentage / sub.total_students
                overall_perc_sum += sub.overall_percentage
            for ts in sub.topic_distribution:
                if ts.total_attempts > 0:
                    ts.average_percentage = ts.average_percentage / ts.total_attempts
                    
        avg_score = (overall_perc_sum / len(subject_data)) if subject_data else 0.0
        
        # Remedial Stats
        completed_remedials = [r for r in remedials if r.status == "completed"]
        total_improvement = sum(sum(r.improvement_metrics.values()) for r in completed_remedials if r.improvement_metrics)
        topic_count = sum(len(r.improvement_metrics) for r in completed_remedials if r.improvement_metrics)
        avg_imp = (total_improvement / topic_count * 100) if topic_count > 0 else None
        
        rem_stats = RemedialStats(
            total_generated=len(remedials),
            total_completed=len(completed_remedials),
            average_improvement_percentage=avg_imp
        )
        
        return TeacherDashboardAnalytics(
            overview=OverviewStats(
                total_assessments=len(assessments),
                total_questions=total_questions,
                total_attempts=len(exams),
                average_score_percentage=avg_score * 100
            ),
            performance_by_subject=list(subject_data.values()),
            remedial_learning=rem_stats
        )

    async def get_student_dashboard(self, student_id: str) -> StudentDashboardAnalytics:
        profiles = await crud_performance.get_multi(filters={"student_id": student_id})
        remedials = await crud_remedial.get_multi(filters={"student_id": student_id})
        
        subject_data: List[SubjectPerformance] = []
        overall_sum = 0
        
        for p in profiles:
            overall_sum += p.overall_percentage
            sub = SubjectPerformance(
                subject=p.subject,
                overall_percentage=p.overall_percentage,
                total_students=1
            )
            for t_name, t_perf in p.topic_performance.items():
                t_stat = TopicStats(
                    topic=t_name,
                    total_attempts=1,
                    average_percentage=t_perf.percentage,
                    weak_count=1 if t_perf.classification == "weak" else 0,
                    strong_count=1 if t_perf.classification == "strong" else 0
                )
                sub.topic_distribution.append(t_stat)
            subject_data.append(sub)
            
        overall = (overall_sum / len(profiles)) if profiles else 0.0
        
        completed_remedials = [r for r in remedials if r.status == "completed"]
        total_improvement = sum(sum(r.improvement_metrics.values()) for r in completed_remedials if r.improvement_metrics)
        topic_count = sum(len(r.improvement_metrics) for r in completed_remedials if r.improvement_metrics)
        avg_imp = (total_improvement / topic_count * 100) if topic_count > 0 else None
        
        rem_stats = RemedialStats(
            total_generated=len(remedials),
            total_completed=len(completed_remedials),
            average_improvement_percentage=avg_imp
        )
        
        return StudentDashboardAnalytics(
            student_id=student_id,
            overall_percentage=overall * 100,
            subject_performance=subject_data,
            remedial_learning=rem_stats
        )

analytics_service = AnalyticsService()
