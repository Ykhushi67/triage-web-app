"""
PatientTriage.ai - Application Configuration.
Uses standard library os.getenv with safe defaults for zero dependency issues.
"""

import os


class Settings:
    APP_NAME: str = "PatientTriage.ai"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # JWT / Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "patient-triage-ai-hackathon-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for prototype

    # Database (SQLite for zero-config prototype)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./patient_triage.db")

    # ML Models directory
    MODELS_DIR: str = os.getenv("MODELS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models")))

    # Confidence threshold below which review is mandatory
    CONFIDENCE_REVIEW_THRESHOLD: float = float(os.getenv("CONFIDENCE_REVIEW_THRESHOLD", "0.72"))

    # Surge Mode thresholds
    INITIAL_OPERATING_MODE: str = os.getenv("INITIAL_OPERATING_MODE", "NORMAL")
    SURGE_QUEUE_THRESHOLD: int = int(os.getenv("SURGE_QUEUE_THRESHOLD", "10"))
    SURGE_WAIT_THRESHOLD_MIN: int = int(os.getenv("SURGE_WAIT_THRESHOLD_MIN", "40"))
    SURGE_CRITICAL_THRESHOLD: int = int(os.getenv("SURGE_CRITICAL_THRESHOLD", "4"))

    # Reassessment timing
    REASSESS_CRITICAL_MIN: int = int(os.getenv("REASSESS_CRITICAL_MIN", "15"))
    REASSESS_MODERATE_MIN: int = int(os.getenv("REASSESS_MODERATE_MIN", "30"))
    REASSESS_LOW_MIN: int = int(os.getenv("REASSESS_LOW_MIN", "60"))


settings = Settings()
