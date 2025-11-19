"""User service for business logic."""
import logging
from app.models import User
from typing import Any, Tuple, List, Dict

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management."""

    @staticmethod
    def get_all_users() -> Tuple[List[Dict[str, Any]], int]:
        """Get all users.
        
        Returns:
            Tuple of (list of user dicts, status code)
        """
        users = User.query.all()
        user_list = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            } for user in users
        ]
        return user_list, 200
