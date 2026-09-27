import random
import math
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from app.crud.crud_question import question as crud_question
from app.crud.crud_assessment import assessment as crud_assessment
from app.schemas.question_paper import QuestionPaperCreate
from app.schemas.question import QuestionInDB
from app.schemas.enums import QuestionStatus

class PaperAssembler:
    
    async def assemble_paper(self, assessment_id: str, version: str = "A") -> QuestionPaperCreate:
        # Fetch Assessment
        assessment = await crud_assessment.get(id=assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        blueprint = assessment.blueprint
        total_questions = blueprint.total_questions
        
        # Calculate distribution targets based on percentages
        diff_targets = self._calculate_targets(blueprint.difficulty_distribution, total_questions)
        type_targets = self._calculate_targets(blueprint.type_distribution, total_questions)
        
        # We fetch all non-rejected questions matching the assessment criteria
        # In a real large DB we would use an aggregation pipeline, but for now we fetch and filter locally
        # or we could construct a MongoDB query.
        query = {
            "subject": assessment.subject,
            "class_level": assessment.class_level,
            "status": {"$ne": QuestionStatus.REJECTED}
        }
        
        if blueprint.topics:
            query["topic"] = {"$in": blueprint.topics}
            
        from app.core.database import db
        cursor = db["questions"].find(query)
        eligible_questions = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            eligible_questions.append(QuestionInDB(**doc))
            
        # Prioritize VALIDATED questions
        eligible_questions.sort(key=lambda q: 0 if q.status == QuestionStatus.VALIDATED else 1)
        
        selected_questions = self._select_questions(eligible_questions, diff_targets, type_targets, total_questions)
        
        if len(selected_questions) < total_questions:
            raise HTTPException(status_code=422, detail=f"Not enough suitable questions in bank. Needed {total_questions}, found {len(selected_questions)} matching blueprint criteria.")
            
        # Shuffle for randomness in variants
        random.shuffle(selected_questions)
        
        paper = QuestionPaperCreate(
            assessment_id=assessment_id,
            version=version,
            total_marks=sum(q.marks for q in selected_questions),
            total_questions=len(selected_questions),
            questions=selected_questions,
            generation_metadata={
                "difficulty_distribution": blueprint.difficulty_distribution,
                "type_distribution": blueprint.type_distribution,
                "topics": blueprint.topics
            }
        )
        return paper
        
    def _calculate_targets(self, distribution: Dict[str, int], total: int) -> Dict[str, int]:
        targets = {}
        for key, percentage in distribution.items():
            if percentage > 0:
                targets[key] = max(1, round((percentage / 100.0) * total))
            else:
                targets[key] = 0
        
        # Adjust rounding errors
        diff = total - sum(targets.values())
        if diff != 0 and targets:
            keys = list(targets.keys())
            targets[keys[0]] += diff
            
        return targets
        
    def _select_questions(self, pool: List[QuestionInDB], diff_targets: Dict[str, int], type_targets: Dict[str, int], total: int) -> List[QuestionInDB]:
        selected = []
        selected_ids = set()
        
        # Copy targets so we can decrement them
        dt = diff_targets.copy()
        tt = type_targets.copy()
        
        for q in pool:
            if len(selected) >= total:
                break
                
            if q.id in selected_ids:
                continue
                
            d_type = q.difficulty.value if hasattr(q.difficulty, 'value') else q.difficulty
            q_type = q.question_type.value if hasattr(q.question_type, 'value') else q.question_type
            
            # Allow selection if targets are not fully met OR if we just need more questions to fill total
            if (dt.get(d_type, 0) > 0 and tt.get(q_type, 0) > 0) or (sum(dt.values()) <= 0 or sum(tt.values()) <= 0):
                selected.append(q)
                selected_ids.add(q.id)
                if d_type in dt: dt[d_type] -= 1
                if q_type in tt: tt[q_type] -= 1
                
        return selected

paper_assembler = PaperAssembler()
