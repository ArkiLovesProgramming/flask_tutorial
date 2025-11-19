"""Authentication service using JWT and Redis for session management."""
import os
import logging
import redis
from typing import Optional, Dict, Any, Tuple
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User
from app.utils.jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
)

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis connection for session storage
# Try to use Celery broker URL if available, otherwise use separate Redis config
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", None)  # Will be parsed from CELERY_BROKER_URL if not set
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_SESSION_DB", "2"))  # Use DB 2 for sessions
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Session TTL (seconds) - should match JWT access token expiry
SESSION_TTL = int(os.getenv("SESSION_TTL", "1800"))  # 30 minutes


def get_redis_client() -> redis.Redis:
    """Get Redis client for session storage.
    
    Parses Redis connection from CELERY_BROKER_URL or uses explicit config.
    
    Returns:
        Redis client instance
    """
    # Parse Redis URL from CELERY_BROKER_URL if available
    if CELERY_BROKER_URL.startswith("redis://"):
        try:
            from urllib.parse import urlparse
            parsed = urlparse(CELERY_BROKER_URL)
            host = REDIS_HOST or parsed.hostname or "127.0.0.1"
            port = REDIS_PORT if REDIS_HOST else (parsed.port or 6379)
            # Extract DB from URL path (e.g., /2) or use default session DB
            url_db = parsed.path.lstrip("/") if parsed.path else None
            db = int(url_db) if url_db and url_db.isdigit() else REDIS_DB
            password = REDIS_PASSWORD or parsed.password
        except Exception as e:
            logger.warning("Failed to parse Redis URL, using defaults: %s", e)
            host = REDIS_HOST or "127.0.0.1"
            port = REDIS_PORT
            db = REDIS_DB
            password = REDIS_PASSWORD
    else:
        host = REDIS_HOST or "127.0.0.1"
        port = REDIS_PORT
        db = REDIS_DB
        password = REDIS_PASSWORD
    
    return redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True,
    )


class AuthService:
    """Authentication service for user login, logout, and session management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
        
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def register_user(username: str, email: str, password: str, role: str = "user") -> Tuple[Dict[str, Any], int]:
        """Register a new user with password.
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            role: User role (default: 'user')
        
        Returns:
            Tuple of (response dict, status code)
        """
        # Validate role
        if role not in ["user", "admin"]:
            logger.warning("Invalid role provided during registration: %s", role)
            return {"error": "Role must be either 'user' or 'admin'"}, 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            logger.warning("User registration failed - user already exists: %s / %s", username, email)
            return {"error": "User with this username or email already exists"}, 409
        
        # Create new user with hashed password
        password_hash = AuthService.hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            logger.info("User registered successfully: %s (%s)", username, email)
            return {"message": "User registered successfully", "id": new_user.id}, 201
        except IntegrityError:
            db.session.rollback()
            logger.warning("User registration failed - duplicate entry: %s / %s", username, email)
            return {"error": "User with this username or email already exists"}, 409
        except Exception as exc:
            db.session.rollback()
            logger.error("Unexpected error registering user: %s", exc, exc_info=True)
            return {"error": "An error occurred while registering the user"}, 500

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password.
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            User object if authentication successful, None otherwise
        """
        user = User.query.filter_by(username=username).first()
        
        if not user:
            logger.warning("Authentication failed - user not found: %s", username)
            return None
        
        if not user.password_hash:
            logger.warning("Authentication failed - user has no password set: %s", username)
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            logger.warning("Authentication failed - invalid password for user: %s", username)
            return None
        
        logger.info("User authenticated successfully: %s", username)
        return user

    @staticmethod
    def login_user(username: str, password: str) -> Tuple[Dict[str, Any], int]:
        """Login a user and generate JWT tokens.
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            Tuple of (response dict with tokens, status code)
        """
        user = AuthService.authenticate_user(username, password)
        
        if not user:
            return {"error": "Invalid username or password"}, 401
        
        # Generate tokens with role
        access_token = generate_access_token(user.id, user.username, user.role)
        refresh_token = generate_refresh_token(user.id, user.username, user.role)
        
        # Store session in Redis for single sign-on
        session_key = f"session:{user.id}:{access_token[:16]}"  # Use token prefix for uniqueness
        redis_client = get_redis_client()
        
        try:
            session_data = {
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role,
                "token": access_token,
            }
            # Store session with TTL
            redis_client.setex(
                session_key,
                SESSION_TTL,
                str(user.id),  # Store user_id as value for quick lookup
            )
            # Also store full session data
            redis_client.setex(
                f"session_data:{user.id}",
                SESSION_TTL,
                str(session_data),
            )
            logger.info("Session stored in Redis for user: %s", username)
        except Exception as e:
            logger.error("Failed to store session in Redis: %s", e, exc_info=True)
            # Continue even if Redis fails - tokens are still valid
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": SESSION_TTL,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
        }, 200

    @staticmethod
    def logout_user(token: str, user_id: int) -> Tuple[Dict[str, Any], int]:
        """Logout a user by invalidating their session.
        
        Args:
            token: JWT access token
            user_id: User ID
        
        Returns:
            Tuple of (response dict, status code)
        """
        redis_client = get_redis_client()
        
        try:
            # Find and remove all sessions for this user
            session_pattern = f"session:{user_id}:*"
            keys = redis_client.keys(session_pattern)
            
            for key in keys:
                redis_client.delete(key)
            
            # Remove session data
            redis_client.delete(f"session_data:{user_id}")
            
            # Also add token to blacklist (optional, for extra security)
            token_prefix = token[:16]
            blacklist_key = f"blacklist:{token_prefix}"
            redis_client.setex(blacklist_key, SESSION_TTL, "1")
            
            logger.info("User logged out successfully: user_id=%s", user_id)
            return {"message": "Logged out successfully"}, 200
        except Exception as e:
            logger.error("Failed to logout user: %s", e, exc_info=True)
            return {"error": "Failed to logout"}, 500

    @staticmethod
    def verify_session(token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token and check if session exists in Redis.
        
        Args:
            token: JWT access token
        
        Returns:
            Decoded token payload if valid and session exists, None otherwise
        """
        # Decode token
        payload = decode_token(token)
        if not payload:
            return None
        
        # Check token type
        if payload.get("type") != "access":
            logger.warning("Invalid token type: %s", payload.get("type"))
            return None
        
        # Check if token is blacklisted
        redis_client = get_redis_client()
        token_prefix = token[:16]
        blacklist_key = f"blacklist:{token_prefix}"
        if redis_client.exists(blacklist_key):
            logger.warning("Token is blacklisted")
            return None
        
        # Check if session exists in Redis
        user_id = payload.get("user_id")
        session_key_pattern = f"session:{user_id}:*"
        session_keys = redis_client.keys(session_key_pattern)
        
        if not session_keys:
            logger.warning("Session not found in Redis for user_id: %s", user_id)
            return None
        
        return payload

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Tuple[Dict[str, Any], int]:
        """Generate a new access token from a refresh token.
        
        Args:
            refresh_token: JWT refresh token
        
        Returns:
            Tuple of (response dict with new access token, status code)
        """
        payload = decode_token(refresh_token)
        
        if not payload:
            return {"error": "Invalid refresh token"}, 401
        
        if payload.get("type") != "refresh":
            return {"error": "Invalid token type"}, 401
        
        user_id = payload.get("user_id")
        username = payload.get("username")
        
        # Get user to verify they still exist
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}, 404
        
        # Generate new access token
        access_token = generate_access_token(user_id, username, user.role)
        
        # Update session in Redis
        redis_client = get_redis_client()
        session_key = f"session:{user_id}:{access_token[:16]}"
        try:
            redis_client.setex(session_key, SESSION_TTL, str(user_id))
            logger.info("Refreshed access token for user: %s", username)
        except Exception as e:
            logger.error("Failed to update session in Redis: %s", e)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": SESSION_TTL,
        }, 200

