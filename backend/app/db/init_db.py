import asyncio
from app.core.database import db

async def init_db():
    print("Initializing database indexes...")
    
    # Questions collection indexes
    await db["questions"].create_index("subject")
    await db["questions"].create_index("class_level")
    await db["questions"].create_index("topic")
    await db["questions"].create_index("difficulty")
    await db["questions"].create_index("blooms_taxonomy")
    await db["questions"].create_index("status")
    await db["questions"].create_index("source")

    # Assessments collection indexes
    await db["assessments"].create_index("subject")
    await db["assessments"].create_index("class_level")
    await db["assessments"].create_index("created_at")
    
    # Question Papers collection indexes
    await db["question_papers"].create_index("assessment_id")
    await db["question_papers"].create_index("version")
    await db["question_papers"].create_index("created_at")
    
    # Exam Sessions collection indexes
    await db["exam_sessions"].create_index("student_id")
    await db["exam_sessions"].create_index("assessment_id")
    await db["exam_sessions"].create_index("status")
    
    print("Database indexes created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
