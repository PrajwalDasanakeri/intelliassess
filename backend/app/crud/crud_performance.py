from typing import List, Optional
from app.schemas.performance import PerformanceProfileCreate, PerformanceProfileInDB, PerformanceProfileUpdate
from app.core.database import db
from bson import ObjectId
from datetime import datetime, timezone

class CRUDPerformanceProfile:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        
    async def get(self, id: str) -> Optional[PerformanceProfileInDB]:
        try:
            object_id = ObjectId(id)
        except Exception:
            return None
        collection = db[self.collection_name]
        doc = await collection.find_one({"_id": object_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return PerformanceProfileInDB(**doc)
        return None

    async def get_by_student_and_subject(self, student_id: str, subject: str) -> Optional[PerformanceProfileInDB]:
        collection = db[self.collection_name]
        doc = await collection.find_one({"student_id": student_id, "subject": subject})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return PerformanceProfileInDB(**doc)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[PerformanceProfileInDB]:
        collection = db[self.collection_name]
        query = filters or {}
        cursor = collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        results = []
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            results.append(PerformanceProfileInDB(**doc))
        return results

    async def create(self, obj_in: PerformanceProfileCreate) -> PerformanceProfileInDB:
        collection = db[self.collection_name]
        doc = obj_in.model_dump()
        
        doc["last_updated"] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return PerformanceProfileInDB(**doc)

    async def update(self, db_obj: PerformanceProfileInDB, obj_in: PerformanceProfileUpdate) -> PerformanceProfileInDB:
        collection = db[self.collection_name]
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Need to handle topic_performance correctly (nested updates can be tricky, but we just override the whole dict here)
        update_data["last_updated"] = datetime.now(timezone.utc)
        
        await collection.update_one(
            {"_id": ObjectId(db_obj.id)},
            {"$set": update_data}
        )
        
        updated_doc = await collection.find_one({"_id": ObjectId(db_obj.id)})
        updated_doc["id"] = str(updated_doc.pop("_id"))
        return PerformanceProfileInDB(**updated_doc)

performance_profile = CRUDPerformanceProfile("performance_profiles")
