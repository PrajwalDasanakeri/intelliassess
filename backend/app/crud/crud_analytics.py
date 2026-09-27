from typing import List, Optional
from app.schemas.analytics import ResearchMetricCreate, ResearchMetricInDB
from app.core.database import db
from bson import ObjectId
from datetime import datetime, timezone

class CRUDResearchMetric:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        
    async def get(self, id: str) -> Optional[ResearchMetricInDB]:
        try:
            object_id = ObjectId(id)
        except Exception:
            return None
        collection = db[self.collection_name]
        doc = await collection.find_one({"_id": object_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return ResearchMetricInDB(**doc)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[ResearchMetricInDB]:
        collection = db[self.collection_name]
        query = filters or {}
        cursor = collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        results = []
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            results.append(ResearchMetricInDB(**doc))
        return results

    async def create(self, obj_in: ResearchMetricCreate) -> ResearchMetricInDB:
        collection = db[self.collection_name]
        doc = obj_in.model_dump()
        
        doc["calculation_timestamp"] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return ResearchMetricInDB(**doc)

research_metric = CRUDResearchMetric("research_metrics")
