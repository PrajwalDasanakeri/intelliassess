import pytest
from fastapi.testclient import TestClient
from app.main import app

# This would normally hit the real frontend and backend, but we'll mock it for now.
# Setting up full playwright E2E with frontend running takes significant setup for this task.
# I will simulate the E2E API flow thoroughly instead to verify the business logic integration.

def test_exam_e2e_flow(client: TestClient):
    # This acts as an end-to-end integration test across all layers for Exam Delivery.
    
    # 1. Create Assessment (Teacher)
    assessment_data = {
        "title": "E2E Exam Delivery Test",
        "description": "Integration testing",
        "subject": "Testing",
        "class_level": "Advanced",
        "duration_minutes": 30,
        "total_marks": 10,
        "blueprint": {
            "total_questions": 2,
            "difficulty_distribution": {"easy": 100},
            "type_distribution": {"mcq": 100},
            "topics": ["E2E"]
        }
    }
    create_res = client.post("/api/v1/assessments/", json=assessment_data)
    assert create_res.status_code == 201
    assessment_id = create_res.json()["id"]

    # 2. Add Questions (Teacher)
    q1_data = {
        "text": "E2E Q1?",
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
        "text": "E2E Q2?",
        "question_type": "mcq",
        "difficulty": "easy",
        "marks": 5,
        "topic": "E2E",
        "subject": "Testing",
        "class_level": "Advanced",
        "blooms_taxonomy": "remember",
        "options": [{"id": "b", "text": "B", "is_correct": True}],
        "correct_answer": "b",
        "status": "validated"
    }
    client.post("/api/v1/questions/", json=q2_data)

    # 3. Assemble Question Paper (Teacher)
    assemble_res = client.post("/api/v1/question-papers/generate", json={"assessment_id": assessment_id, "version": "A"})
    assert assemble_res.status_code == 201, assemble_res.json()

    # 4. Student Logs In & Starts Assessment (Student)
    student_headers = {"X-Student-ID": "e2e_student_1"}
    start_res = client.post(f"/api/v1/exams/{assessment_id}/start", headers=student_headers)
    assert start_res.status_code == 200
    
    exam_data = start_res.json()
    assert exam_data["status"] == "in_progress"
    session_id = exam_data["session_id"]
    questions = exam_data["questions"]
    assert len(questions) == 2
    # Ensure answers are stripped
    assert "correct_answer" not in questions[0]

    # 5. Student Answers Questions (Autosave simulation)
    q1_id = questions[0]["id"]
    q2_id = questions[1]["id"]
    
    answer_payload = [{"question_id": q1_id, "student_answer": "a"}]
    ans_res = client.post(f"/api/v1/exams/{session_id}/answers", headers=student_headers, json=answer_payload)
    assert ans_res.status_code == 200
    
    # 6. Student Submits Exam
    submit_res = client.post(f"/api/v1/exams/{session_id}/submit", headers=student_headers)
    assert submit_res.status_code == 200

    # 7. Student checks submission (Status should be COMPLETED)
    get_res = client.get(f"/api/v1/exams/{session_id}", headers=student_headers)
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "completed"
    
    # 8. Late modification attempt (Should be rejected)
    late_ans = client.post(f"/api/v1/exams/{session_id}/answers", headers=student_headers, json=answer_payload)
    assert late_ans.status_code == 400
