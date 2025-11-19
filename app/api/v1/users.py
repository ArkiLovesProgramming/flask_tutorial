"""User endpoints."""
import logging
from time import sleep

from app import cache
from app.services.user_service import UserService
from app.utils.auth_decorator import require_auth, require_role

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60


@cache.memoize(timeout=CACHE_TTL_SECONDS)
def _load_user_from_source(user_id: str) -> str:
    """Simulate a slow data source and cache the payload."""
    logger.info("Fetching user %s from slow backend", user_id)
    sleep(5)
    return f"User {user_id} data"


def get_user(user_id: str):
    """Return cached user data."""
    payload = _load_user_from_source(user_id)
    return payload


@require_auth
@require_role("admin")
def list_users():
    """List all users (Admin only)."""
    return UserService.get_all_users()
