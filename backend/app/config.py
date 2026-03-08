"""
Configuration management for Federated Healthcare Intelligence
Loads settings from environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"


class Settings(BaseSettings):
    """Application settings from environment"""
    
    # Application
    APP_NAME: str = "Federated Healthcare Intelligence"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database (SQLite local)
    DATABASE_URL: str = "mysql+pymysql://root:newpassword@localhost:3306/federated_healthcare"
    DB_ECHO: bool = False
    
    # Security & Auth
    SECRET_KEY: str = "test-secret-key-change-in-production"
    ADMIN_SECRET_KEY: str = "test-admin-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours (1 day)
    
    # Storage (local)
    UPLOAD_DIR: str = str(PROJECT_ROOT / "storage" / "datasets")
    MODEL_DIR: str = str(PROJECT_ROOT / "models")
    LOG_DIR: str = str(LOG_DIR)
    
    # Federated Learning
    FEDERATED_ROUNDS: int = 100
    LOCAL_EPOCHS: int = 5
    MIN_HOSPITALS: int = 2  # Minimum for aggregation
    
    # Differential Privacy (Phase 8+)
    EPSILON: float = 0.5
    DELTA: float = 1e-5
    
    # AI Summarization (Gemini API)
    GEMINI_API_KEY: str = "AIzaSyBqhyDEtKMhS4zVWHGt5zwvPMTGslZeXd4"
    GEMINI_MODEL: str = "gemini-3-flash"  # or gemini-1.5-pro
    ENABLE_AI_SUMMARIES: bool = True
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Email/SMTP Configuration (Phase 31)
    SMTP_HOST: str = ""  # e.g., "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@federated-health.local"
    SMTP_USE_TLS: bool = True
    EMAIL_ENABLED: bool = False  # Set to True to enable email notifications
    
    # Notification Settings (Phase 31)
    NOTIFICATION_RETENTION_DAYS: int = 30
    MAX_NOTIFICATIONS_PER_USER: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()
