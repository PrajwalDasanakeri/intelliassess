import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List
from pydantic import BaseModel

from app.schemas.question_paper import QuestionPaperInDB
from app.crud.crud_question_paper import question_paper as crud_question_paper
from app.crud.crud_assessment import assessment as crud_assessment
from app.services.paper_assembler import paper_assembler
from app.services.pdf_generator import PDFGenerator

router = APIRouter()

class GeneratePaperRequest(BaseModel):
    assessment_id: str
    version: str = "A"

@router.post("/generate", response_model=QuestionPaperInDB, status_code=201)
async def generate_paper(request: GeneratePaperRequest):
    # Assemble paper logically
    paper_create = await paper_assembler.assemble_paper(
        assessment_id=request.assessment_id, 
        version=request.version
    )
    # Save to DB
    return await crud_question_paper.create(obj_in=paper_create)

@router.get("/", response_model=List[QuestionPaperInDB])
async def list_papers(skip: int = 0, limit: int = 100):
    return await crud_question_paper.get_multi(skip=skip, limit=limit)

@router.get("/{id}", response_model=QuestionPaperInDB)
async def get_paper(id: str):
    p = await crud_question_paper.get(id=id)
    if not p:
        raise HTTPException(status_code=404, detail="Question paper not found")
    return p

@router.get("/{id}/preview", response_model=QuestionPaperInDB)
async def preview_paper(id: str):
    p = await crud_question_paper.get(id=id)
    if not p:
        raise HTTPException(status_code=404, detail="Question paper not found")
    # For now preview just returns the JSON. A specialized response could be tailored here
    return p

@router.delete("/{id}", status_code=204)
async def delete_paper(id: str):
    success = await crud_question_paper.delete(id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Question paper not found")

@router.get("/{id}/pdf")
async def get_paper_pdf(id: str):
    p = await crud_question_paper.get(id=id)
    if not p:
        raise HTTPException(status_code=404, detail="Question paper not found")
        
    assessment = await crud_assessment.get(id=p.assessment_id)
    
    pdf_gen = PDFGenerator()
    os.makedirs("/tmp/pdfs", exist_ok=True)
    file_path = f"/tmp/pdfs/paper_{id}.pdf"
    
    pdf_gen.generate_question_paper_pdf(p, assessment, file_path)
    
    return FileResponse(
        path=file_path, 
        filename=f"IntelliAssess_Version_{p.version}.pdf",
        media_type='application/pdf'
    )
