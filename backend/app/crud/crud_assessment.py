from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import db
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate, AssessmentInDB

class CRUDAssessment:
    collection_name = "assessments"

    async def get(self, id: str) -> Optional[AssessmentInDB]:
        document = await db[self.collection_name].find_one({"_id": ObjectId(id)})
        if document:
            document["id"] = str(document.pop("_id"))
            return AssessmentInDB(**document)
        return None

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[AssessmentInDB]:
        cursor = db[self.collection_name].find().skip(skip).limit(limit)
        assessments = []
        async for document in cursor:
            document["id"] = str(document.pop("_id"))
            assessments.append(AssessmentInDB(**document))
        return assessments

    async def create(self, obj_in: AssessmentCreate) -> AssessmentInDB:
        document = obj_in.model_dump()
        document["created_at"] = datetime.now(timezone.utc)
        document["updated_at"] = datetime.now(timezone.utc)
        result = await db[self.collection_name].insert_one(document)
        document["id"] = str(result.inserted_id)
        return AssessmentInDB(**document)

    async def update(self, id: str, obj_in: AssessmentUpdate) -> Optional[AssessmentInDB]:
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

assessment = CRUDAssessment()
