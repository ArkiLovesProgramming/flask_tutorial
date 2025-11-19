"""Development environment configuration."""
import os

from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    # Development config can have defaults, but prefer .env file
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///instance/db/test.db",
    )
    CELERY_BROKER_URL = os.getenv(
        "CELERY_BROKER_URL",
        "redis://127.0.0.1:6379/0",
    )
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://127.0.0.1:6379/1",
    )

