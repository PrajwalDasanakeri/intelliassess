import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from sentence_transformers import SentenceTransformer, util

from app.crud.crud_exam import crud_exam
from app.crud.crud_question import question as crud_question
from app.crud.crud_question_paper import question_paper as crud_question_paper
from app.crud.crud_evaluation import evaluation as crud_evaluation
from app.schemas.exam import ExamStatus, ExamSessionUpdate
from app.schemas.question import QuestionInDB
from app.schemas.enums import QuestionType
from app.schemas.evaluation import (
    EvaluationCreate, 
    EvaluationMethod, 
    EvaluationCriterion, 
    LLMEvaluationResult
)
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

class SemanticSimilarityService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Load a lightweight sentence transformer model lazily
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def calculate_similarity(cls, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        model = cls.get_model()
        emb1 = model.encode(text1, convert_to_tensor=True)
        emb2 = model.encode(text2, convert_to_tensor=True)
        cosine_scores = util.cos_sim(emb1, emb2)
        return float(cosine_scores[0][0])

class AnswerEvaluationService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.semantic_service = SemanticSimilarityService()

    async def evaluate_exam(self, exam_session_id: str) -> List[Any]:
        # 1. Retrieve completed exam
        exam = await crud_exam.get(id=exam_session_id)
        if not exam:
            raise ValueError("Exam session not found")
        
        if exam.status != ExamStatus.COMPLETED:
            raise ValueError(f"Exam cannot be evaluated because it is {exam.status}")

        # Check if already evaluated to prevent duplicate records
        existing_evals = await crud_evaluation.get_by_exam_session(exam_session_id)
        if existing_evals:
            raise ValueError("Exam has already been evaluated")

        # 2. Retrieve responses and questions
        responses = exam.responses
        
        paper = None
        if exam.question_paper_id:
            paper = await crud_question_paper.get(id=exam.question_paper_id)
        
        results = []
        
        for response in responses:
            question_id = response.question_id
            question = await crud_question.get(id=question_id)
            if not question:
                continue

            response_id = str(uuid.uuid4()) # Generate a pseudo response_id
            
            # Determine evaluation type
            if question.question_type in [QuestionType.MCQ, QuestionType.TRUE_FALSE]:
                eval_record = await self._evaluate_objective(exam.id, exam.student_id, question, response.student_answer, response_id)
            elif question.question_type == QuestionType.SHORT_ANSWER:
                eval_record = await self._evaluate_short_answer(exam.id, exam.student_id, question, response.student_answer, response_id)
            else:
                eval_record = await self._evaluate_descriptive(exam.id, exam.student_id, question, response.student_answer, response_id)
            
            if eval_record:
                saved_eval = await crud_evaluation.create(obj_in=eval_record)
                results.append(saved_eval)

        # Update exam status to GRADED
        await crud_exam.update(
            id=exam.id,
            obj_in=ExamSessionUpdate(status=ExamStatus.GRADED)
        )
        
        # Trigger performance analysis and profile update
        from app.services.performance_service import performance_service
        await performance_service.analyze_exam_and_update_profile(exam.id)
        
        return results

    async def _evaluate_objective(self, exam_session_id: str, student_id: str, question: QuestionInDB, student_answer: Any, response_id: str) -> EvaluationCreate:
        awarded = 0.0
        
        # Check against correct_answer or correct option
        if question.question_type == QuestionType.MCQ:
            # find correct option
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            if correct_option and str(student_answer) == str(correct_option.id):
                awarded = float(question.marks)
        elif question.question_type == QuestionType.TRUE_FALSE:
            # Assume correct_answer holds 'true' or 'false'
            if str(student_answer).lower() == str(question.correct_answer).lower():
                awarded = float(question.marks)

        return EvaluationCreate(
            exam_session_id=exam_session_id,
            student_id=student_id,
            question_id=question.id,
            response_id=response_id,
            awarded_marks=awarded,
            maximum_marks=float(question.marks),
            evaluation_method=EvaluationMethod.OBJECTIVE,
            confidence_score=1.0,
            ai_feedback="Correct" if awarded > 0 else "Incorrect"
        )

    async def _evaluate_short_answer(self, exam_session_id: str, student_id: str, question: QuestionInDB, student_answer: Any, response_id: str) -> EvaluationCreate:
        expected = question.correct_answer or ""
        student_ans = str(student_answer) if student_answer else ""
        
        if not student_ans.strip():
            return EvaluationCreate(
                exam_session_id=exam_session_id,
                student_id=student_id,
                question_id=question.id,
                response_id=response_id,
                awarded_marks=0.0,
                maximum_marks=float(question.marks),
                evaluation_method=EvaluationMethod.SEMANTIC,
                confidence_score=1.0,
                ai_feedback="No answer provided."
            )

        similarity = self.semantic_service.calculate_similarity(expected, student_ans)
        
        awarded = 0.0
        feedback = "Incorrect"
        # simple heuristic
        if similarity > 0.85:
            awarded = float(question.marks)
            feedback = "Correct."
        elif similarity > 0.6:
            awarded = float(question.marks) * 0.5
            feedback = "Partially correct."
            
        return EvaluationCreate(
            exam_session_id=exam_session_id,
            student_id=student_id,
            question_id=question.id,
            response_id=response_id,
            awarded_marks=awarded,
            maximum_marks=float(question.marks),
            evaluation_method=EvaluationMethod.SEMANTIC,
            confidence_score=similarity,
            ai_feedback=feedback
        )

    async def _evaluate_descriptive(self, exam_session_id: str, student_id: str, question: QuestionInDB, student_answer: Any, response_id: str) -> EvaluationCreate:
        student_ans = str(student_answer) if student_answer else ""
        if not student_ans.strip():
            return EvaluationCreate(
                exam_session_id=exam_session_id,
                student_id=student_id,
                question_id=question.id,
                response_id=response_id,
                awarded_marks=0.0,
                maximum_marks=float(question.marks),
                evaluation_method=EvaluationMethod.LLM,
                confidence_score=1.0,
                ai_feedback="No answer provided."
            )

        prompt = f"""
You are an expert AI evaluator for educational assessments. Evaluate the following student answer.

Question: {question.text}
Expected Answer/Rubric: {question.correct_answer or question.explanation or 'Evaluate generally on correctness.'}
Student Answer: {student_ans}
Maximum Marks: {question.marks}
Learning Objective: {question.blooms_taxonomy.value.upper()}
Topic: {question.topic}

Instructions:
1. Evaluate ONLY the supplied student answer.
2. Follow the expected answer/rubric closely.
3. Award partial credit when justified.
4. NEVER exceed the maximum marks ({question.marks}).
5. Return a structured JSON object.
6. Provide concise, constructive feedback.
7. Do not invent facts.

Required JSON format:
{{
    "awarded_marks": float,
    "maximum_marks": float,
    "confidence_score": float (0.0 to 1.0),
    "feedback": "string",
    "criteria": [
        {{
            "criterion": "string",
            "marks_awarded": float,
            "reason": "string"
        }}
    ]
}}
"""
        try:
            llm_response = await self.llm_client.generate_json(prompt)
            # Validate with Pydantic
            validated = LLMEvaluationResult(**llm_response)
            
            return EvaluationCreate(
                exam_session_id=exam_session_id,
                student_id=student_id,
                question_id=question.id,
                response_id=response_id,
                awarded_marks=validated.awarded_marks,
                maximum_marks=float(question.marks),
                evaluation_method=EvaluationMethod.LLM,
                confidence_score=validated.confidence_score,
                ai_feedback=validated.feedback,
                criteria=validated.criteria
            )
        except Exception as e:
            logger.error(f"LLM evaluation failed: {str(e)}")
            return EvaluationCreate(
                exam_session_id=exam_session_id,
                student_id=student_id,
                question_id=question.id,
                response_id=response_id,
                awarded_marks=0.0,
                maximum_marks=float(question.marks),
                evaluation_method=EvaluationMethod.LLM,
                confidence_score=0.0,
                ai_feedback="Evaluation failed due to an internal error."
            )
