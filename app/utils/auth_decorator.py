"""Authentication decorator for protecting routes."""
import logging
from functools import wraps
from flask import request, jsonify
from typing import Callable, Any

from app.utils.jwt_utils import get_token_from_header, decode_token
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication for a route.
    
    Usage:
        @require_auth
        def protected_route():
            # Access current user via request.current_user
            return {"user_id": request.current_user["user_id"]}
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        token = get_token_from_header(auth_header)
        
        if not token:
            logger.warning("Authentication required but no token provided")
            return jsonify({"error": "Authentication required"}), 401
        
        # Verify token and session
        payload = AuthService.verify_session(token)
        
        if not payload:
            logger.warning("Invalid or expired token")
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Attach user info to request object
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f: Callable) -> Callable:
    """Decorator for optional authentication.
    
    If a valid token is provided, request.current_user will be set.
    If no token or invalid token, request.current_user will be None.
    
    Usage:
        @optional_auth
        def public_route():
            if hasattr(request, 'current_user') and request.current_user:
                # User is authenticated
                return {"user_id": request.current_user["user_id"]}
            else:
                # Public access
                return {"message": "Public content"}
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization")
        token = get_token_from_header(auth_header)
        
        if token:
            payload = AuthService.verify_session(token)
            if payload:
                request.current_user = payload
            else:
                request.current_user = None
        else:
            request.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(role: str) -> Callable:
    """Decorator to require a specific role for a route.
    
    Must be used AFTER @require_auth or in conjunction with token verification.
    
    Usage:
        @require_auth
        @require_role("admin")
        def admin_route():
            return {"message": "Admin only"}
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Ensure user is authenticated (request.current_user must be set by require_auth)
            if not hasattr(request, 'current_user') or not request.current_user:
                logger.warning("Role check failed: User not authenticated")
                return jsonify({"error": "Authentication required"}), 401
            
            user_role = request.current_user.get("role")
            if user_role != role:
                logger.warning("Role check failed: User role '%s' != required '%s'", user_role, role)
                return jsonify({"error": "Forbidden: Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator