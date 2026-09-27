from fastapi import APIRouter

from app.api.api_v1.endpoints import questions, assessments, question_papers, exams, performance, remedial, analytics, research

api_router = APIRouter()

@api_router.get("/health")
def health_check():
    return {"status": "ok"}

api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(question_papers.router, prefix="/question-papers", tags=["question-papers"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])
api_router.include_router(remedial.router, prefix="/remedial", tags=["remedial"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
