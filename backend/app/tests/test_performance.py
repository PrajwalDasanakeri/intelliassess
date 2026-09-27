import pytest
from unittest.mock import patch
from app.crud.crud_performance import performance_profile as crud_performance
from app.crud.crud_remedial import remedial_test as crud_remedial
from app.schemas.performance import PerformanceProfileCreate, TopicPerformance, RemedialTestCreate
from app.core.config import settings

class MockLLMClient:
    async def generate_json(self, prompt: str) -> dict:
        return {
            "awarded_marks": 5,
            "maximum_marks": 5,
            "confidence_score": 0.9,
            "feedback": "Excellent answer.",
            "criteria": []
        }

@pytest.fixture
def mock_llm_client():
    return MockLLMClient()

def setup_exam(client, student_id: str):
    assessment_data = {
        "title": "Performance Test",
        "description": "Perf test",
        "subject": "Testing",
        "class_level": "Advanced",
        "duration_minutes": 30,
        "total_marks": 5,
        "blueprint": {
            "total_questions": 1,
            "difficulty_distribution": {"easy": 100},
            "type_distribution": {"mcq": 100},
            "topics": ["Testing_Topic"]
        }
    }
    create_res = client.post("/api/v1/assessments/", json=assessment_data)
    assessment_id = create_res.json()["id"]

    q1_data = {
        "text": "Q1 MCQ?",
        "question_type": "mcq",
        "difficulty": "easy",
        "marks": 5,
        "topic": "Testing_Topic",
        "subject": "Testing",
        "class_level": "Advanced",
        "blooms_taxonomy": "remember",
        "options": [{"id": "a", "text": "A", "is_correct": True}],
        "correct_answer": "a",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q1_data)
    client.post("/api/v1/question-papers/generate", json={"assessment_id": assessment_id, "version": "A"})
    
    student_headers = {"X-Student-ID": student_id}
    start_res = client.post(f"/api/v1/exams/{assessment_id}/start", headers=student_headers)
    session_id = start_res.json()["session_id"]
    questions = start_res.json()["questions"]
    
    answers = [{"question_id": questions[0]["id"], "student_answer": "a"}]
    client.post(f"/api/v1/exams/{session_id}/answers", headers=student_headers, json=answers)
    client.post(f"/api/v1/exams/{session_id}/submit", headers=student_headers)
    
    return assessment_id, session_id

def test_performance_calculation_and_weak_topic_detection(client, mock_llm_client):
    student_id = "perf_student_1"
    student_headers = {"X-Student-ID": student_id}
    assessment_id, session_id = setup_exam(client, student_id)
    
    with patch("app.api.api_v1.endpoints.exams.llm_client", mock_llm_client):
        client.post(f"/api/v1/exams/{session_id}/evaluate", headers=student_headers)
    
    res = client.get("/api/v1/performance/my-profile?subject=Testing", headers=student_headers)
    assert res.status_code == 200
    profiles = res.json()
    assert len(profiles) > 0
    profile = profiles[0]
    
    assert profile["total_questions_encountered"] > 0
    assert profile["total_maximum_marks"] > 0
    
    topic_perf = profile["topic_performance"]["Testing_Topic"]
    assert topic_perf["total_questions"] > 0
    
    if topic_perf["percentage"] < settings.WEAK_TOPIC_THRESHOLD:
        assert topic_perf["classification"] == "weak"
    elif topic_perf["percentage"] >= settings.STRONG_TOPIC_THRESHOLD:
        assert topic_perf["classification"] == "strong"
    else:
        assert topic_perf["classification"] == "average"

@pytest.mark.asyncio
async def test_remedial_test_generation(client):
    student_id = "perf_student_2"
    student_headers = {"X-Student-ID": student_id}
    subject = "Math"
    
    await crud_performance.create(obj_in=PerformanceProfileCreate(
        student_id=student_id,
        subject=subject,
        class_level="Grade 10",
        weak_topics=["Algebra"],
        topic_performance={"Algebra": TopicPerformance(topic="Algebra", percentage=0.4, classification="weak")}
    ))
    
    res = client.post(f"/api/v1/remedial/generate?subject={subject}", headers=student_headers)
    assert res.status_code == 201
    remedial = res.json()
    
    assert remedial["selected_difficulty"] == "easy"
    assert "Algebra" in remedial["weak_topics_targeted"]
    assert remedial["performance_snapshot_before"]["Algebra"] == 0.4
    assert remedial["status"] == "generated"

@pytest.mark.asyncio
async def test_remedial_improvement_calculation(client, mock_llm_client):
    student_id = "perf_student_3"
    student_headers = {"X-Student-ID": student_id}
    assessment_id, session_id = setup_exam(client, student_id)
    
    # Create the remedial test pointing to this exam session
    remedial = await crud_remedial.create(obj_in=RemedialTestCreate(
        student_id=student_id,
        subject="Testing",
        class_level="Advanced",
        assessment_id=assessment_id,
        weak_topics_targeted=["Testing_Topic"],
        selected_difficulty="easy",
        exam_session_id=session_id,
        performance_snapshot_before={"Testing_Topic": 0.2} # Previously weak
    ))
    
    # Evaluate which triggers performance service -> which updates remedial test improvement
    with patch("app.api.api_v1.endpoints.exams.llm_client", mock_llm_client):
        client.post(f"/api/v1/exams/{session_id}/evaluate", headers=student_headers)
    
    # Check the updated remedial test
    updated_remedial = await crud_remedial.get(id=remedial.id)
    assert updated_remedial.status == "completed"
    assert "Testing_Topic" in updated_remedial.improvement_metrics
    assert updated_remedial.improvement_metrics["Testing_Topic"] > 0 

def test_unauthorized_student_access(client):
    student_headers = {"X-Student-ID": "unauth_student"}
    res = client.get("/api/v1/performance/weak-topics?subject=Testing", headers=student_headers)
    assert res.status_code == 200
    assert res.json() == [] 

    res = client.get("/api/v1/remedial/507f1f77bcf86cd799439011", headers=student_headers)
    assert res.status_code == 404
