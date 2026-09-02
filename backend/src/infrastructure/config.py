"""
Application configuration
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment"""
    
    # General
    env: str = "development"
    api_title: str = "MFIT → Hevy Orchestrator"
    api_version: str = "0.1.0"
    api_description: str = "Sistema seguro para importar fichas de treino do MFIT para o Hevy"
    
    # Database
    database_url: str = "sqlite:///./data/mfit_hevy.db"
    
    # Hevy API
    hevy_api_base_url: str = "https://api.hevyapp.com"
    hevy_api_key: str = ""
    hevy_api_timeout: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
