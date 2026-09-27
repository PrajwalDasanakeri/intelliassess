QUESTION_GENERATION_PROMPT = """
You are an expert educator. Generate a question matching the following criteria:
- Subject: {subject}
- Class/Grade: {class_level}
- Topic: {topic}
- Learning Objective: {learning_objective}
- Question Type: {question_type}
- Difficulty: {difficulty}
- Bloom's Taxonomy Level: {blooms_taxonomy}
- Marks: {marks}

Respond ONLY with a valid JSON object matching this schema. Do not include markdown code blocks or any other text.
{{
    "text": "The question text",
    "question_type": "{question_type}",
    "difficulty": "{difficulty}",
    "blooms_taxonomy": "{blooms_taxonomy}",
    "subject": "{subject}",
    "topic": "{topic}",
    "class_level": "{class_level}",
    "correct_answer": "The correct answer as text (if not MCQ)",
    "explanation": "Detailed explanation of the answer",
    "options": [
        {{"id": "A", "text": "Option 1", "is_correct": true}},
        {{"id": "B", "text": "Option 2", "is_correct": false}}
    ] // Only include options array if question_type is 'mcq'
}}
"""
