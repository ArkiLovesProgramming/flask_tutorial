"""Base configuration shared across all environments."""
import os


def _get_secret_key():
    """Get SECRET_KEY from environment variable.
    
    Raises:
        ValueError: If SECRET_KEY is not set
    """
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError(
            "SECRET_KEY environment variable is required. "
            "Please set it in .env file or as an environment variable."
        )
    return secret_key


class BaseConfig:
    """Base configuration shared across environments."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = "SimpleCache"
    # SECRET_KEY must be set via environment variable
    # For development, use .env file. For production, set via environment.
    SECRET_KEY = _get_secret_key()

