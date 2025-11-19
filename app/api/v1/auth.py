"""Authentication endpoints for login, logout, and token management."""
import logging
from flask import request

from app.services.auth_service import AuthService
from app.utils.auth_decorator import require_auth

logger = logging.getLogger(__name__)


def login(body: dict = None):
    """Login endpoint - authenticate user and return JWT tokens.
    
    Args:
        body: Request body containing username and password
    
    Returns:
        JSON response with access_token and refresh_token
    """
    if not body:
        return {"error": "Request body is required"}, 400
    
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        logger.warning("Login attempt with missing credentials")
        return {"error": "Username and password are required"}, 400
    
    return AuthService.login_user(username, password)


def register(body: dict = None):
    """Register endpoint - create a new user account.
    
    Args:
        body: Request body containing username, email, password, and optional role
    
    Returns:
        JSON response with user creation status
    """
    if not body:
        return {"error": "Request body is required"}, 400
    
    username = body.get("username")
    email = body.get("email")
    password = body.get("password")
    role = body.get("role", "user")  # Default to 'user' if not provided
    
    if not username or not email or not password:
        return {"error": "Username, email, and password are required"}, 400
    
    if len(password) < 6:
        return {"error": "Password must be at least 6 characters long"}, 400
    
    # Validate role
    if role not in ["user", "admin"]:
        return {"error": "Role must be either 'user' or 'admin'"}, 400
    
    return AuthService.register_user(username, email, password, role)


@require_auth
def logout():
    """Logout endpoint - invalidate user session.
    
    Requires authentication via Authorization header.
    
    Returns:
        JSON response with logout status
    """
    user_id = request.current_user.get("user_id")
    auth_header = request.headers.get("Authorization")
    
    # Extract token from header
    token = None
    if auth_header:
        try:
            _, token = auth_header.split(" ", 1)
        except ValueError:
            pass
    
    if not token:
        return {"error": "Token not found"}, 400
    
    return AuthService.logout_user(token, user_id)


def refresh(body: dict = None):
    """Refresh access token using refresh token.
    
    Args:
        body: Request body containing refresh_token
    
    Returns:
        JSON response with new access_token
    """
    if not body:
        return {"error": "Request body is required"}, 400
    
    refresh_token = body.get("refresh_token")
    
    if not refresh_token:
        return {"error": "refresh_token is required"}, 400
    
    return AuthService.refresh_access_token(refresh_token)


@require_auth
def me():
    """Get current user information.
    
    Requires authentication via Authorization header.
    
    Returns:
        JSON response with current user information
    """
    user_info = {
        "user_id": request.current_user.get("user_id"),
        "username": request.current_user.get("username"),
    }
    
    return user_info, 200

