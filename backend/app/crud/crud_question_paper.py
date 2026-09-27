from typing import Optional, List, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from app.core.database import db
from app.schemas.question_paper import QuestionPaperCreate, QuestionPaperUpdate, QuestionPaperInDB
from bson import ObjectId

class CRUDQuestionPaper:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.collection = db[collection_name]

    async def get(self, id: str) -> Optional[QuestionPaperInDB]:
        document = await self.collection.find_one({"_id": ObjectId(id)})
        if document:
            document["id"] = str(document.pop("_id"))
            return QuestionPaperInDB(**document)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100, filters: Optional[dict] = None) -> List[QuestionPaperInDB]:
        query = filters or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        results = []
        async for document in cursor:
            document["id"] = str(document.pop("_id"))
            results.append(QuestionPaperInDB(**document))
        return results

    async def create(self, obj_in: QuestionPaperCreate) -> QuestionPaperInDB:
        document = obj_in.model_dump()
        document["created_at"] = datetime.now(timezone.utc)
        document["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.insert_one(document)
        document["id"] = str(result.inserted_id)
        return QuestionPaperInDB(**document)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

question_paper = CRUDQuestionPaper("question_papers")
