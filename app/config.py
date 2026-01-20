# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
import secrets


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "KYC Backend System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_ECHO: bool = False
    
    # Redis - OPTIONAL (set to None if not using)
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False
    
    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_PATH: str = "./data/documents"
    STORAGE_BUCKET_DOCUMENTS: str = "documents"
    STORAGE_BUCKET_PHOTOS: str = "photos"

    # Make MinIO settings optional:
    STORAGE_ENDPOINT: Optional[str] = None
    STORAGE_ACCESS_KEY: Optional[str] = None
    STORAGE_SECRET_KEY: Optional[str] = None
    STORAGE_BUCKET_DOCUMENTS: str = "documents"  # Used by local storage too
    STORAGE_BUCKET_PHOTOS: str = "photos"
    STORAGE_SECURE: bool = False
    
    # Document Processing
    OCR_ENGINE: str = "easyocr"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    OCR_LANGUAGES: List[str] = ["ar", "fr", "en"]
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "application/pdf"
    ]

    ALLOWED_ORIGINS: List[str] = ["http://localhost:8000"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # AI Models
    FACE_RECOGNITION_MODEL: str = "facenet"
    LIVENESS_DETECTION_ENABLED: bool = True
    MIN_FACE_MATCH_SCORE: float = 0.90
    
    # KYC
    CIN_REGEX: str = r"^[A-Z]{1,2}\d{6,7}$"
    AUTO_APPROVE_THRESHOLD: float = 0.95
    MANUAL_REVIEW_THRESHOLD: float = 0.75
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()