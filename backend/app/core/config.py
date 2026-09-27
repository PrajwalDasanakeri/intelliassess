from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntelliAssess"
    API_V1_STR: str = "/api/v1"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "intelliassess"
    LLM_PROVIDER: str = "ollama"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    WEAK_TOPIC_THRESHOLD: float = 0.50
    STRONG_TOPIC_THRESHOLD: float = 0.80

    class Config:
        env_file = ".env"

settings = Settings()
