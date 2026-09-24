import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "jobs"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Content Automation Engine"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./content_engine.db"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    OPENROUTER_API_KEY: str = ""
    DEFAULT_RESEARCH_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    DEFAULT_WRITER_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    DEFAULT_QUALITY_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"

    
    STRAPI_URL: str = "http://localhost:1337"
    STRAPI_API_TOKEN: str = ""
    STRAPI_CONTENT_TYPE: str = "articles"
    
    DEMO_MODE: bool = True
    MAX_REVISION_ATTEMPTS: int = 3
    STORAGE_PATH: Path = STORAGE_DIR
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

os.makedirs(settings.STORAGE_PATH, exist_ok=True)
