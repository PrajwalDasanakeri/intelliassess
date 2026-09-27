import pytest
from unittest.mock import patch
from app.main import app
from app.services.llm_client import LLMClient

class MockLLMClient(LLMClient):
    async def generate_json(self, prompt: str) -> dict:
        return {
            "text": "What is the capital of France?",
            "question_type": "mcq",
            "difficulty": "easy",
            "blooms_taxonomy": "remember",
            "subject": "Geography",
            "topic": "World Capitals",
            "class_level": "Grade 5",
            "correct_answer": "Paris",
            "explanation": "Paris is the capital of France.",
            "options": [
                {"id": "A", "text": "Paris", "is_correct": True},
                {"id": "B", "text": "London", "is_correct": False}
            ]
        }

def test_generate_question(client):
    with patch("app.api.api_v1.endpoints.questions.llm_client", MockLLMClient()):
        response = client.post(
            "/api/v1/questions/generate",
            json={
                "subject": "Geography",
                "class_level": "Grade 5",
                "topic": "World Capitals",
                "learning_objective": "Identify capitals",
                "question_type": "mcq",
                "difficulty": "easy",
                "blooms_taxonomy": "remember",
                "marks": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == "What is the capital of France?"
        assert data["source"] == "ai_generated"
        assert data["status"] == "draft"
        assert "id" in data
        
        # Clean up
        client.delete(f"/api/v1/questions/{data['id']}")
