import time
import logging
from app.celery_app import celery

logger = logging.getLogger(__name__)

@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def add(self, x: int, y: int):
    """Simple add task that can optionally run within Flask app context.
    
    Args:
        x: First number
        y: Second number
    
    Returns:
        Sum of x and y
    """
    logger.info(f"Executing add task: {x} + {y}")
    logger.debug(f"Celery broker URL: {celery.conf.broker_url}")
    time.sleep(1)  # Simulate processing time
    
    # If app is available, run within app context
    if hasattr(celery, 'app') and celery.app is not None:
        with celery.app.app_context():
            # Database operations can go here
            pass
    
    result = x + y
    logger.info(f"Task completed: {x} + {y} = {result}")
    return result
