from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionInDB
from app.crud.crud_question import question as crud_question
from app.services.question_generator import QuestionGenerator
from app.services.ollama_client import llm_client

router = APIRouter()

class QuestionGenerateRequest(BaseModel):
    subject: str
    class_level: str
    topic: str
    learning_objective: str
    question_type: str
    difficulty: str
    blooms_taxonomy: str
    marks: int = 1

@router.post("/generate", response_model=QuestionInDB, status_code=201)
async def generate_and_save_question(request: QuestionGenerateRequest):
    generator = QuestionGenerator(llm_client=llm_client)
    question_create = await generator.generate_question(request.model_dump())
    return await crud_question.create(obj_in=question_create)

@router.post("/", response_model=QuestionInDB, status_code=201)
async def create_question(question_in: QuestionCreate):
    return await crud_question.create(obj_in=question_in)

@router.get("/{id}", response_model=QuestionInDB)
async def get_question(id: str):
    q = await crud_question.get(id=id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q

@router.get("/", response_model=List[QuestionInDB])
async def list_questions(skip: int = 0, limit: int = 100):
    return await crud_question.get_multi(skip=skip, limit=limit)

@router.put("/{id}", response_model=QuestionInDB)
async def update_question(id: str, question_in: QuestionUpdate):
    q = await crud_question.update(id=id, obj_in=question_in)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q

@router.delete("/{id}", status_code=204)
async def delete_question(id: str):
    success = await crud_question.delete(id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
