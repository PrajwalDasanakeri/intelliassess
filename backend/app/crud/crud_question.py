from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import db
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionInDB

class CRUDQuestion:
    collection_name = "questions"

    async def get(self, id: str) -> Optional[QuestionInDB]:
        document = await db[self.collection_name].find_one({"_id": ObjectId(id)})
        if document:
            document["id"] = str(document.pop("_id"))
            return QuestionInDB(**document)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[QuestionInDB]:
        query = filters or {}
        cursor = db[self.collection_name].find(query).skip(skip).limit(limit)
        questions = []
        async for document in cursor:
            document["id"] = str(document.pop("_id"))
            questions.append(QuestionInDB(**document))
        return questions

    async def create(self, obj_in: QuestionCreate) -> QuestionInDB:
        document = obj_in.model_dump()
        document["created_at"] = datetime.now(timezone.utc)
        document["updated_at"] = datetime.now(timezone.utc)
        result = await db[self.collection_name].insert_one(document)
        document["id"] = str(result.inserted_id)
        return QuestionInDB(**document)

    async def update(self, id: str, obj_in: QuestionUpdate) -> Optional[QuestionInDB]:
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

    async def delete(self, id: str) -> bool:
        result = await db[self.collection_name].delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

question = CRUDQuestion()
