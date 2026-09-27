from typing import List, Optional
from app.schemas.evaluation import EvaluationCreate, EvaluationInDB, EvaluationUpdate
from app.core.database import db
from bson import ObjectId

class CRUDEvaluation:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        
    async def get(self, id: str) -> Optional[EvaluationInDB]:
        collection = db[self.collection_name]
        doc = await collection.find_one({"_id": ObjectId(id)})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return EvaluationInDB(**doc)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[EvaluationInDB]:
        collection = db[self.collection_name]
        query = filters or {}
        cursor = collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        results = []
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            results.append(EvaluationInDB(**doc))
        return results

    async def get_by_exam_session(self, exam_session_id: str) -> List[EvaluationInDB]:
        return await self.get_multi(filters={"exam_session_id": exam_session_id}, limit=1000)

    async def create(self, obj_in: EvaluationCreate) -> EvaluationInDB:
        collection = db[self.collection_name]
        doc = obj_in.model_dump()
        
        from datetime import datetime, timezone
        doc["created_at"] = datetime.now(timezone.utc)
        doc["updated_at"] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return EvaluationInDB(**doc)

    async def update(self, db_obj: EvaluationInDB, obj_in: EvaluationUpdate) -> EvaluationInDB:
        collection = db[self.collection_name]
        update_data = obj_in.model_dump(exclude_unset=True)
        
        from datetime import datetime, timezone
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await collection.update_one(
            {"_id": ObjectId(db_obj.id)},
            {"$set": update_data}
        )
        
        updated_doc = await collection.find_one({"_id": ObjectId(db_obj.id)})
        updated_doc["id"] = str(updated_doc.pop("_id"))
        return EvaluationInDB(**updated_doc)
        
    async def delete(self, id: str) -> bool:
        collection = db[self.collection_name]
        result = await collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

evaluation = CRUDEvaluation("evaluations")
