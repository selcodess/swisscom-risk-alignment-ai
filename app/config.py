from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Swisscom RiskAlign AI"
    environment: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./riskalign.db"
    gemini_api_key: Optional[str] = None
    cors_origins: list[str] = [
        "http://localhost:4200",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
