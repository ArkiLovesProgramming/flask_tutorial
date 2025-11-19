"""Health check endpoints."""
import logging

logger = logging.getLogger(__name__)


def ping():
    """Return a simple health payload."""
    logger.debug("Health check requested")
    return {"ok": True}

