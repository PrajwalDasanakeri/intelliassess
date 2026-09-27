def test_create_assessment(client):
    response = client.post(
        "/api/v1/assessments/",
        json={
            "title": "Midterm Geography",
            "description": "Standard geography test",
            "subject": "Geography",
            "class_level": "Grade 5",
            "blueprint": {
                "total_questions": 10,
                "difficulty_distribution": {"easy": 5, "medium": 3, "hard": 2},
                "type_distribution": {"mcq": 10},
                "topics": ["World Capitals"]
            },
            "duration_minutes": 60,
            "total_marks": 100,
            "question_ids": []
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Midterm Geography"
    assert "id" in data

    # Clean up
    client.delete(f"/api/v1/assessments/{data['id']}")

def test_get_assessments(client):
    response = client.get("/api/v1/assessments/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
