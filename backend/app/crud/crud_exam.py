from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import db
from app.schemas.exam import ExamSessionCreate, ExamSessionUpdate, ExamSessionInDB, StudentResponse

class CRUDExamSession:
    collection_name = "exam_sessions"

    async def get(self, id: str) -> Optional[ExamSessionInDB]:
        document = await db[self.collection_name].find_one({"_id": ObjectId(id)})
        if document:
            document["id"] = str(document.pop("_id"))
            return ExamSessionInDB(**document)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[ExamSessionInDB]:
        query = filters or {}
        cursor = db[self.collection_name].find(query).skip(skip).limit(limit)
        sessions = []
        async for document in cursor:
            document["id"] = str(document.pop("_id"))
            sessions.append(ExamSessionInDB(**document))
        return sessions

    async def create(self, obj_in: ExamSessionCreate) -> ExamSessionInDB:
        document = obj_in.model_dump()
        document["created_at"] = datetime.now(timezone.utc)
        document["updated_at"] = datetime.now(timezone.utc)
        document["responses"] = []
        result = await db[self.collection_name].insert_one(document)
        document["id"] = str(result.inserted_id)
        return ExamSessionInDB(**document)

    async def update(self, id: str, obj_in: ExamSessionUpdate) -> Optional[ExamSessionInDB]:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get(id)
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db[self.collection_name].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get(id)
        return None

    async def update_responses(self, id: str, responses: List[StudentResponse]) -> Optional[ExamSessionInDB]:
        update_data = {
            "responses": [r.model_dump() for r in responses],
            "updated_at": datetime.now(timezone.utc)
        }
        result = await db[self.collection_name].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get(id)
        return await self.get(id)

    async def get_active_session(self, student_id: str, assessment_id: str) -> Optional[ExamSessionInDB]:
        document = await db[self.collection_name].find_one({
            "student_id": student_id,
            "assessment_id": assessment_id,
            "status": {"$in": ["not_started", "in_progress"]}
        })
        if document:
            document["id"] = str(document.pop("_id"))
            return ExamSessionInDB(**document)
        return None

crud_exam = CRUDExamSession()
