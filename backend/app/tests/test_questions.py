def test_create_question(client):
    response = client.post(
        "/api/v1/questions/",
        json={
            "text": "What is the capital of France?",
            "question_type": "mcq",
            "difficulty": "easy",
            "blooms_taxonomy": "remember",
            "subject": "Geography",
            "topic": "World Capitals",
            "class_level": "Grade 5",
            "options": [
                {"id": "A", "text": "Paris", "is_correct": True},
                {"id": "B", "text": "London", "is_correct": False}
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "What is the capital of France?"
    assert "id" in data
    
    # Clean up (for test predictability)
    client.delete(f"/api/v1/questions/{data['id']}")

def test_get_questions(client):
    response = client.get("/api/v1/questions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
