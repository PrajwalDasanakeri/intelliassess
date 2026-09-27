from typing import List, Optional
from app.schemas.performance import RemedialTestCreate, RemedialTestInDB, RemedialTestUpdate
from app.core.database import db
from bson import ObjectId
from datetime import datetime, timezone

class CRUDRemedialTest:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        
    async def get(self, id: str) -> Optional[RemedialTestInDB]:
        try:
            object_id = ObjectId(id)
        except Exception:
            return None
        collection = db[self.collection_name]
        doc = await collection.find_one({"_id": object_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return RemedialTestInDB(**doc)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[RemedialTestInDB]:
        collection = db[self.collection_name]
        query = filters or {}
        cursor = collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        results = []
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            results.append(RemedialTestInDB(**doc))
        return results

    async def create(self, obj_in: RemedialTestCreate) -> RemedialTestInDB:
        collection = db[self.collection_name]
        doc = obj_in.model_dump()
        
        doc["created_at"] = datetime.now(timezone.utc)
        doc["updated_at"] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return RemedialTestInDB(**doc)

    async def update(self, db_obj: RemedialTestInDB, obj_in: RemedialTestUpdate) -> RemedialTestInDB:
        collection = db[self.collection_name]
        update_data = obj_in.model_dump(exclude_unset=True)
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await collection.update_one(
            {"_id": ObjectId(db_obj.id)},
            {"$set": update_data}
        )
        
        updated_doc = await collection.find_one({"_id": ObjectId(db_obj.id)})
        updated_doc["id"] = str(updated_doc.pop("_id"))
        return RemedialTestInDB(**updated_doc)

remedial_test = CRUDRemedialTest("remedial_tests")
