"""Production environment configuration."""
import os

from .base import BaseConfig


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    # All production config values must come from environment variables
    # No defaults - fail fast if missing
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "")

    @classmethod
    def validate(cls):
        """Validate required environment variables."""
        required_vars = {
            "SECRET_KEY": cls.SECRET_KEY,
            "DATABASE_URL": cls.SQLALCHEMY_DATABASE_URI,
            "CELERY_BROKER_URL": cls.CELERY_BROKER_URL,
            "CELERY_RESULT_BACKEND": cls.CELERY_RESULT_BACKEND,
        }
        missing = [var for var, value in required_vars.items() if not value]
        if missing:
            raise ValueError(
                "Production requires the following environment variables: "
                + ", ".join(missing)
            )

