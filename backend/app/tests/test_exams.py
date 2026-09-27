import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.schemas.exam import ExamSessionInDB, ExamStatus

def mock_get_assessment(id):
    from app.schemas.assessment import AssessmentInDB, AssessmentBlueprint
    if id == "valid_exam_test":
        return AssessmentInDB(
            id="valid_exam_test",
            title="Test",
            description="Test",
            subject="Math",
            class_level="Grade 1",
            duration_minutes=60,
            total_marks=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            blueprint=AssessmentBlueprint(
                total_questions=2,
                difficulty_distribution={"easy": 50, "medium": 50, "hard": 0},
                type_distribution={"mcq": 100},
                topics=["Addition"]
            )
        )
    return None

def mock_get_paper_multi(filters, limit):
    from app.schemas.question_paper import QuestionPaperInDB
    if filters.get("assessment_id") == "valid_exam_test":
        return [QuestionPaperInDB(
            id="paper_1",
            assessment_id="valid_exam_test",
            version="A",
            total_marks=2,
            total_questions=2,
            questions=[],
            generation_metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )]
    return []

@pytest.mark.asyncio
async def test_start_exam_api(client):
    with patch("app.services.exam_service.crud_assessment.get", side_effect=mock_get_assessment):
        with patch("app.services.exam_service.crud_exam.get_active_session", return_value=None):
            with patch("app.services.exam_service.crud_question_paper.get_multi", side_effect=mock_get_paper_multi):
                with patch("app.services.exam_service.crud_exam.create") as mock_create:
                    mock_create.return_value = ExamSessionInDB(
                        id="session_1",
                        student_id="student_1",
                        assessment_id="valid_exam_test",
                        question_paper_id="paper_1",
                        status=ExamStatus.IN_PROGRESS,
                        start_time=datetime.now(timezone.utc),
                        end_time=datetime.now(timezone.utc) + timedelta(minutes=60),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    
                    response = client.post("/api/v1/exams/valid_exam_test/start", headers={"X-Student-ID": "student_1"})
                    assert response.status_code == 200
                    assert response.json()["session_id"] == "session_1"
                    assert response.json()["assessment_id"] == "valid_exam_test"
                    assert response.json()["status"] == "in_progress"

@pytest.mark.asyncio
async def test_submit_exam_api(client):
    with patch("app.api.api_v1.endpoints.exams.exam_service.complete_exam", return_value={"status": "success"}):
        response = client.post("/api/v1/exams/session_1/submit", headers={"X-Student-ID": "student_1"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_submit_answers_api(client):
    with patch("app.api.api_v1.endpoints.exams.exam_service.submit_answers", return_value={"status": "success"}):
        response = client.post("/api/v1/exams/session_1/answers", headers={"X-Student-ID": "student_1"}, json=[
            {"question_id": "q1", "student_answer": "A"}
        ])
        assert response.status_code == 200
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_unauthorized_exam_access(client):
    # No header provided
    response = client.post("/api/v1/exams/session_1/submit")
    assert response.status_code == 422 # FastAPI validation error for missing header
