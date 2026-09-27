from typing import Dict, Any
from app.services.llm_client import LLMClient
from app.services.prompts import QUESTION_GENERATION_PROMPT
from app.schemas.question import QuestionCreate
from app.schemas.enums import SourceType, QuestionStatus
from fastapi import HTTPException

class QuestionGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def generate_question(self, params: Dict[str, Any]) -> QuestionCreate:
        prompt = QUESTION_GENERATION_PROMPT.format(
            subject=params.get("subject", ""),
            class_level=params.get("class_level", ""),
            topic=params.get("topic", ""),
            learning_objective=params.get("learning_objective", ""),
            question_type=params.get("question_type", ""),
            difficulty=params.get("difficulty", ""),
            blooms_taxonomy=params.get("blooms_taxonomy", ""),
            marks=params.get("marks", 1)
        )
        
        # Call LLM
        json_data = await self.llm_client.generate_json(prompt)
        
        # Enforce metadata overrides
        json_data["source"] = SourceType.AI_GENERATED
        json_data["status"] = QuestionStatus.DRAFT
        
        # Validate with Pydantic
        try:
            validated_question = QuestionCreate(**json_data)
            return validated_question
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM output validation failed: {str(e)}")
