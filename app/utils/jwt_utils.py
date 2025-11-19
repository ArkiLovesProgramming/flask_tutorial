"""JWT utility functions for token generation and validation."""
import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# JWT configuration
# JWT_SECRET_KEY defaults to SECRET_KEY if not set, but SECRET_KEY should always be set
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY or SECRET_KEY environment variable is required. "
        "Please set it in .env file or as an environment variable."
    )
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def generate_access_token(user_id: int, username: str, role: str = 'user', additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """Generate a JWT access token.
    
    Args:
        user_id: User ID
        username: Username
        role: User role (user/admin)
        additional_claims: Additional claims to include in the token
    
    Returns:
        Encoded JWT token string
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug("Generated access token for user_id: %s, role: %s", user_id, role)
    return token


def generate_refresh_token(user_id: int, username: str, role: str = 'user') -> str:
    """Generate a JWT refresh token.
    
    Args:
        user_id: User ID
        username: Username
        role: User role
    
    Returns:
        Encoded JWT refresh token string
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug("Generated refresh token for user_id: %s", user_id)
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token: %s", e)
        return None


def get_token_from_header(auth_header: Optional[str]) -> Optional[str]:
    """Extract token from Authorization header.
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")
    
    Returns:
        Token string if valid format, None otherwise
    """
    if not auth_header:
        return None
    
    try:
        scheme, token = auth_header.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None
