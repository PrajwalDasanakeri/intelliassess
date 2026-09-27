import pytest
from unittest.mock import patch, MagicMock
from app.schemas.exam import ExamStatus
from app.schemas.enums import QuestionType, BloomsTaxonomy, DifficultyLevel, SourceType
from app.schemas.evaluation import EvaluationMethod
from app.services.evaluation_service import AnswerEvaluationService

class MockLLMClient:
    async def generate_json(self, prompt: str) -> dict:
        return {
            "awarded_marks": 5,
            "maximum_marks": 5,
            "confidence_score": 0.9,
            "feedback": "Excellent answer.",
            "criteria": [
                {
                    "criterion": "Clarity",
                    "marks_awarded": 5,
                    "reason": "Very clear."
                }
            ]
        }

@pytest.fixture
def mock_llm_client():
    return MockLLMClient()

@pytest.fixture
def mock_semantic_service():
    with patch("app.services.evaluation_service.SemanticSimilarityService.calculate_similarity") as mock:
        yield mock

def test_evaluation_objective(client, mock_llm_client):
    # 1. Setup Assessment and Question Paper
    assessment_data = {
        "title": "Objective Eval Test",
        "description": "Eval test",
        "subject": "Testing",
        "class_level": "Advanced",
        "duration_minutes": 30,
        "total_marks": 10,
        "blueprint": {
            "total_questions": 2,
            "difficulty_distribution": {"easy": 100},
            "type_distribution": {"mcq": 50, "true_false": 50},
            "topics": ["E2E"]
        }
    }
    create_res = client.post("/api/v1/assessments/", json=assessment_data)
    assessment_id = create_res.json()["id"]

    q1_data = {
        "text": "E2E Q1 MCQ?",
        "question_type": "mcq",
        "difficulty": "easy",
        "marks": 5,
        "topic": "E2E",
        "subject": "Testing",
        "class_level": "Advanced",
        "blooms_taxonomy": "remember",
        "options": [{"id": "a", "text": "A", "is_correct": True}],
        "correct_answer": "a",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q1_data)

    q2_data = {
        "text": "True or False?",
        "question_type": "true_false",
        "difficulty": "easy",
        "marks": 5,
        "topic": "E2E",
        "subject": "Testing",
        "class_level": "Advanced",
        "blooms_taxonomy": "remember",
        "correct_answer": "true",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q2_data)

    assemble_res = client.post("/api/v1/question-papers/generate", json={"assessment_id": assessment_id, "version": "A"})
    
    # 2. Complete Exam
    student_headers = {"X-Student-ID": "eval_student"}
    start_res = client.post(f"/api/v1/exams/{assessment_id}/start", headers=student_headers)
    session_id = start_res.json()["session_id"]
    questions = start_res.json()["questions"]
    
    # MCQ correct, TF incorrect
    q_mcq = next(q for q in questions if q["question_type"] == "mcq")
    q_tf = next(q for q in questions if q["question_type"] == "true_false")
    
    answers = [
        {"question_id": q_mcq["id"], "student_answer": "a"},
        {"question_id": q_tf["id"], "student_answer": "false"}
    ]
    client.post(f"/api/v1/exams/{session_id}/answers", headers=student_headers, json=answers)
    client.post(f"/api/v1/exams/{session_id}/submit", headers=student_headers)
    
    # 3. Evaluate
    with patch("app.api.api_v1.endpoints.exams.llm_client", mock_llm_client):
        eval_res = client.post(f"/api/v1/exams/{session_id}/evaluate", headers=student_headers)
    
    assert eval_res.status_code == 200, eval_res.json()
    evaluations = eval_res.json()
    assert len(evaluations) == 2
    
    # Check results
    for ev in evaluations:
        if ev["question_id"] == q_mcq["id"]:
            assert ev["awarded_marks"] == 5.0
            assert ev["evaluation_method"] == "objective"
        elif ev["question_id"] == q_tf["id"]:
            assert ev["awarded_marks"] == 0.0
            assert ev["evaluation_method"] == "objective"
            
    # Check status is GRADED
    get_res = client.get(f"/api/v1/exams/{session_id}", headers=student_headers)
    assert get_res.json()["status"] == "graded"

def test_evaluation_subjective(client, mock_llm_client, mock_semantic_service):
    # Setup Assessment and Question Paper
    assessment_data = {
        "title": "Subjective Eval Test",
        "description": "Eval test",
        "subject": "Testing",
        "class_level": "Advanced",
        "duration_minutes": 30,
        "total_marks": 10,
        "blueprint": {
            "total_questions": 2,
            "difficulty_distribution": {"easy": 100},
            "type_distribution": {"short_answer": 50, "long_answer": 50},
            "topics": ["E2E"]
        }
    }
    create_res = client.post("/api/v1/assessments/", json=assessment_data)
    assessment_id = create_res.json()["id"]

    q1_data = {
        "text": "Short ans?",
        "question_type": "short_answer",
        "difficulty": "easy",
        "marks": 5,
        "topic": "E2E",
        "subject": "Testing",
        "class_level": "Advanced",
        "blooms_taxonomy": "remember",
        "correct_answer": "Short correct",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q1_data)

    q2_data = {
        "text": "Descriptive ans?",
        "question_type": "long_answer",
        "difficulty": "easy",
        "marks": 5,
        "topic": "E2E",
        "subject": "Testing",
        "class_level": "Advanced",
        "blooms_taxonomy": "remember",
        "correct_answer": "Long correct",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q2_data)

    client.post("/api/v1/question-papers/generate", json={"assessment_id": assessment_id, "version": "A"})
    
    student_headers = {"X-Student-ID": "eval_student_2"}
    start_res = client.post(f"/api/v1/exams/{assessment_id}/start", headers=student_headers)
    session_id = start_res.json()["session_id"]
    questions = start_res.json()["questions"]
    
    q_short = next(q for q in questions if q["question_type"] == "short_answer")
    q_long = next(q for q in questions if q["question_type"] == "long_answer")
    
    answers = [
        {"question_id": q_short["id"], "student_answer": "Short partially correct"},
        {"question_id": q_long["id"], "student_answer": "This is a detailed descriptive answer."}
    ]
    client.post(f"/api/v1/exams/{session_id}/answers", headers=student_headers, json=answers)
    client.post(f"/api/v1/exams/{session_id}/submit", headers=student_headers)
    
    mock_semantic_service.return_value = 0.7 # Partial credit for short answer
    
    with patch("app.api.api_v1.endpoints.exams.llm_client", mock_llm_client):
        eval_res = client.post(f"/api/v1/exams/{session_id}/evaluate", headers=student_headers)
    
    assert eval_res.status_code == 200
    evaluations = eval_res.json()
    assert len(evaluations) == 2
    
    for ev in evaluations:
        if ev["question_id"] == q_short["id"]:
            assert ev["awarded_marks"] == 2.5 # 0.5 * 5
            assert ev["evaluation_method"] == "semantic"
        elif ev["question_id"] == q_long["id"]:
            assert ev["awarded_marks"] == 5.0 # From mock llm
            assert ev["evaluation_method"] == "llm"

def test_invalid_evaluation_state(client, mock_llm_client):
    student_headers = {"X-Student-ID": "eval_student_3"}
    assessment_data = {
        "title": "Invalid Eval Test",
        "description": "Eval test",
        "subject": "Testing",
        "class_level": "Advanced",
        "duration_minutes": 30,
        "total_marks": 5,
        "blueprint": {
            "total_questions": 1,
            "difficulty_distribution": {"easy": 100},
            "type_distribution": {"mcq": 100},
            "topics": ["E2E"]
        }
    }
    create_res = client.post("/api/v1/assessments/", json=assessment_data)
    assessment_id = create_res.json()["id"]

    q1_data = {
        "text": "E2E Q1 MCQ?",
        "question_type": "mcq",
        "difficulty": "easy",
        "marks": 5,
        "topic": "E2E",
        "subject": "Testing",
        "class_level": "Advanced",
        "blooms_taxonomy": "remember",
        "options": [{"id": "a", "text": "A", "is_correct": True}],
        "correct_answer": "a",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q1_data)
    client.post("/api/v1/question-papers/generate", json={"assessment_id": assessment_id, "version": "A"})
    
    start_res = client.post(f"/api/v1/exams/{assessment_id}/start", headers=student_headers)
    session_id = start_res.json()["session_id"]
    
    # Try to evaluate IN_PROGRESS exam
    eval_res = client.post(f"/api/v1/exams/{session_id}/evaluate", headers=student_headers)
    assert eval_res.status_code == 400
    assert "cannot be evaluated" in eval_res.json()["detail"]
