import pytest
from app.schemas.enums import QuestionType, DifficultyLevel, BloomsTaxonomy, QuestionStatus
from app.schemas.question import QuestionInDB
from app.schemas.assessment import AssessmentInDB, AssessmentBlueprint
from app.services.paper_assembler import paper_assembler
from unittest.mock import patch
from datetime import datetime, timezone

def mock_get_assessment(id):
    if id == "valid":
        return AssessmentInDB(
            id="valid",
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

class MockCursor:
    def __init__(self, items):
        self.items = items
    def __aiter__(self):
        self.iter = iter(self.items)
        return self
    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

def mock_find(query):
    # Return 3 mock questions
    return MockCursor([
        {
            "_id": "q1", "text": "1+1?", "question_type": "mcq", "difficulty": "easy",
            "blooms_taxonomy": "remember", "subject": "Math", "topic": "Addition",
            "class_level": "Grade 1", "marks": 1, "status": "validated", "source": "manual",
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": "q2", "text": "2+2?", "question_type": "mcq", "difficulty": "medium",
            "blooms_taxonomy": "remember", "subject": "Math", "topic": "Addition",
            "class_level": "Grade 1", "marks": 1, "status": "validated", "source": "manual",
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
        }
    ])

@pytest.mark.asyncio
async def test_assemble_paper():
    with patch("app.services.paper_assembler.crud_assessment.get", side_effect=mock_get_assessment):
        with patch("app.core.database.db") as mock_db:
            mock_db.__getitem__.return_value.find.side_effect = mock_find
            paper = await paper_assembler.assemble_paper("valid")
            assert paper.assessment_id == "valid"
            assert paper.total_questions == 2
            assert paper.total_marks == 2
            assert len(paper.questions) == 2
            
def test_generate_paper_api(client):
    with patch("app.api.api_v1.endpoints.question_papers.paper_assembler.assemble_paper") as mock_assemble:
        from app.schemas.question_paper import QuestionPaperCreate
        mock_assemble.return_value = QuestionPaperCreate(
            assessment_id="valid",
            version="A",
            total_marks=2,
            total_questions=2,
            questions=[]
        )
        response = client.post("/api/v1/question-papers/generate", json={
            "assessment_id": "valid",
            "version": "A"
        })
        assert response.status_code == 201
        assert response.json()["total_questions"] == 2
        assert response.json()["total_marks"] == 2
        assert response.json()["version"] == "A"

def test_pdf_generation_api(client):
    with patch("app.api.api_v1.endpoints.question_papers.crud_question_paper.get") as mock_get_paper:
        with patch("app.api.api_v1.endpoints.question_papers.crud_assessment.get") as mock_get_assessment_api:
            with patch("app.api.api_v1.endpoints.question_papers.PDFGenerator.generate_question_paper_pdf") as mock_pdf_generate:
                from app.schemas.question_paper import QuestionPaperInDB
                mock_get_paper.return_value = QuestionPaperInDB(
                    id="paper_1",
                    assessment_id="valid",
                    version="A",
                    total_marks=2,
                    total_questions=2,
                    questions=[],
                    generation_metadata={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                mock_get_assessment_api.return_value = mock_get_assessment("valid")
                mock_pdf_generate.return_value = "/tmp/mock.pdf"
                
                # Mock FileResponse to prevent actually trying to read the file
                with patch("app.api.api_v1.endpoints.question_papers.FileResponse") as mock_file_response:
                    mock_file_response.return_value = {"filename": "mock.pdf"}
                    response = client.get("/api/v1/question-papers/paper_1/pdf")
                    assert response.status_code == 200

@pytest.mark.asyncio
async def test_duplicate_prevention_in_assembly():
    with patch("app.services.paper_assembler.crud_assessment.get", side_effect=mock_get_assessment):
        with patch("app.core.database.db") as mock_db:
            # Provide the same question twice in the cursor to test duplication logic
            def mock_find_duplicates(query):
                return MockCursor([
                    {
                        "_id": "q1", "text": "1+1?", "question_type": "mcq", "difficulty": "easy",
                        "blooms_taxonomy": "remember", "subject": "Math", "topic": "Addition",
                        "class_level": "Grade 1", "marks": 1, "status": "validated", "source": "manual",
                        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
                    },
                    {
                        "_id": "q1", "text": "1+1?", "question_type": "mcq", "difficulty": "easy",
                        "blooms_taxonomy": "remember", "subject": "Math", "topic": "Addition",
                        "class_level": "Grade 1", "marks": 1, "status": "validated", "source": "manual",
                        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
                    },
                    {
                        "_id": "q2", "text": "2+2?", "question_type": "mcq", "difficulty": "medium",
                        "blooms_taxonomy": "remember", "subject": "Math", "topic": "Addition",
                        "class_level": "Grade 1", "marks": 1, "status": "validated", "source": "manual",
                        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
                    }
                ])
            mock_db.__getitem__.return_value.find.side_effect = mock_find_duplicates
            
            paper = await paper_assembler.assemble_paper("valid")
            # Should still be 2 questions, ignoring the duplicate q1
            assert paper.total_questions == 2
            assert len(paper.questions) == 2
            question_ids = [q.id for q in paper.questions]
            assert "q1" in question_ids
            assert "q2" in question_ids
            # Ensure q1 only appears once
            assert question_ids.count("q1") == 1
