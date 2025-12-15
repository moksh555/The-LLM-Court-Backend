import os
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Config(BaseSettings):
    APP_NAME: str = "LLM Court Backend Service"
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    CORS_ORIGINS: List[str] = ["localhost:8000", "http://localhost:3000"]
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")

    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    OPENROUTER_STAGE_1_PLAINTIFF_MODEL: str = "openai/gpt-5.2-chat"
    OPENROUTER_STAGE_1_DEFENSE_MODEL: str = "x-ai/grok-4-fast"

    JURY_MODELS: List[str] = [
        "openai/gpt-4o-mini-2024-07-18",
        "google/gemini-2.5-flash-lite",
        "mistralai/devstral-2512",
    ]

    JUDGE_MODEL: str = "x-ai/grok-4.1-fast"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Config()
