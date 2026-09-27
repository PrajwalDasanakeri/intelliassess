import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.schemas.analytics import ResearchMetricCreate
from app.crud.crud_assessment import assessment as crud_assessment
from app.crud.crud_question import question as crud_question
from app.crud.crud_question_paper import question_paper as crud_question_paper
from app.crud.crud_analytics import research_metric as crud_analytics

@pytest.fixture
def test_client(client):
    return client

def setup_analytics_data(client):
    assessment_data = {
        "title": "Analytics Test",
        "description": "Analytics test",
        "subject": "Math",
        "class_level": "Grade 10",
        "duration_minutes": 30,
        "total_marks": 10,
        "blueprint": {
            "total_questions": 2,
            "difficulty_distribution": {"easy": 50, "medium": 50},
            "type_distribution": {"mcq": 100},
            "topics": ["Algebra", "Geometry"]
        }
    }
    create_res = client.post("/api/v1/assessments/", json=assessment_data)
    assessment_id = create_res.json()["id"]

    q1_data = {
        "text": "Q1 Algebra",
        "question_type": "mcq",
        "difficulty": "easy",
        "marks": 5,
        "topic": "Algebra",
        "subject": "Math",
        "class_level": "Grade 10",
        "blooms_taxonomy": "remember",
        "options": [{"id": "a", "text": "A", "is_correct": True}],
        "correct_answer": "a",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q1_data)

    q2_data = {
        "text": "Q2 Geometry",
        "question_type": "mcq",
        "difficulty": "medium",
        "marks": 5,
        "topic": "Geometry",
        "subject": "Math",
        "class_level": "Grade 10",
        "blooms_taxonomy": "remember",
        "options": [{"id": "a", "text": "A", "is_correct": True}],
        "correct_answer": "a",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q2_data)

    client.post("/api/v1/question-papers/generate", json={"assessment_id": assessment_id, "version": "A"})
    
    return assessment_id

def test_calculate_research_metrics(test_client):
    teacher_headers = {"X-Teacher-ID": "test_teacher"}
    assessment_id = setup_analytics_data(test_client)
    
    res = test_client.post(f"/api/v1/research/calculate/{assessment_id}", headers=teacher_headers)
    assert res.status_code == 200
    metrics = res.json()
    assert len(metrics) > 0
    
    # Verify Uniqueness
    u_metric = next((m for m in metrics if m["metric_type"] == "uniqueness"), None)
    assert u_metric is not None
    assert u_metric["status"] == "calculated"
    assert "Semantic similarity using SentenceTransformer" in u_metric["calculation_method"] or "all-MiniLM-L6-v2" in u_metric["calculation_method"]
    assert u_metric["value"] >= 0 and u_metric["value"] <= 100
    
    # Verify Syllabus/Topic Alignment
    sa_metric = next((m for m in metrics if m["metric_type"] == "alignment"), None)
    assert sa_metric is not None
    assert sa_metric["metric_name"] == "Topic Alignment"
    assert "learning-objective" in sa_metric["limitations"]
    assert sa_metric["value"] == 100.0 # Both questions match the topics
    
    # Verify Difficulty Consistency
    dc_metric = next((m for m in metrics if m["metric_type"] == "consistency"), None)
    assert dc_metric is not None
    assert dc_metric["value"] == 100.0 # 50/50 exactly matches blueprint
    
    # Verify Evaluation Accuracy is insufficient data
    ea_metric = next((m for m in metrics if m["metric_type"] == "accuracy"), None)
    assert ea_metric is not None
    assert ea_metric["status"] == "insufficient_data"
    
def test_get_research_metrics(test_client):
    teacher_headers = {"X-Teacher-ID": "test_teacher"}
    res = test_client.get("/api/v1/research/metrics", headers=teacher_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_teacher_analytics_dashboard(test_client):
    teacher_headers = {"X-Teacher-ID": "test_teacher"}
    res = test_client.get("/api/v1/analytics/overview/teacher", headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert "overview" in data
    assert "performance_by_subject" in data
    assert "remedial_learning" in data

def test_student_analytics_dashboard(test_client):
    student_headers = {"X-Student-ID": "test_student_1"}
    res = test_client.get("/api/v1/analytics/overview/student", headers=student_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["student_id"] == "test_student_1"
    assert "overall_percentage" in data
    assert "subject_performance" in data
    assert "remedial_learning" in data
