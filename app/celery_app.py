"""Celery application configuration and initialization.

This module provides Celery configuration compatible with Celery 5.x.
Celery 5.x uses lowercase configuration keys without the CELERY_ prefix.
"""
import os
from celery import Celery
from kombu import Exchange, Queue

# Read broker and backend URLs from environment variables
# These are used as fallback defaults if not provided via Flask config
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")

# Create Celery instance with default broker and backend
celery = Celery(
    "app",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks"],
)

# Safe and commonly used default values
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    task_acks_late=True,                 # ACK after task completion
    worker_prefetch_multiplier=1,        # Prevent long tasks from starving
    task_reject_on_worker_lost=True,     # Allow retry on worker disconnect
)

# Queue and routing configuration (can be extended as needed)
# Define custom queue with exchange
celery.conf.task_queues = (
    Queue("default", Exchange("tasks"), routing_key="default", durable=True),
)

# Set default queue, exchange, and routing key
# This ensures all tasks are sent to the "default" queue unless explicitly specified
celery.conf.task_default_queue = "default"
celery.conf.task_default_exchange = "tasks"
celery.conf.task_default_exchange_type = "direct"
celery.conf.task_default_routing_key = "default"


def init_celery(app=None):
    """Initialize Celery with Flask app context support.
    
    This function converts Flask configuration keys (using CELERY_ prefix)
    to Celery 5.x compatible format (lowercase without prefix).
    
    Celery 5.x no longer supports mixing old and new configuration keys.
    This function ensures compatibility by converting all Flask config
    keys to the new format before updating Celery configuration.
    
    Args:
        app: Flask application instance. If provided, Celery will be
             configured with values from Flask's config object.
    
    Returns:
        Celery: The configured Celery instance.
    
    Example:
        >>> from app import create_app
        >>> app = create_app()
        >>> celery = init_celery(app)
    """
    if app is not None:
        # Convert Flask config to Celery 5.x compatible format
        # Celery 5.x uses lowercase keys without CELERY_ prefix
        celery_config = {}
        
        # Map Flask config keys (CELERY_*) to Celery 5.x format (lowercase)
        # This ensures compatibility with Celery 5.x which doesn't allow
        # mixing old and new configuration key formats
        config_mapping = {
            'CELERY_BROKER_URL': 'broker_url',
            'CELERY_RESULT_BACKEND': 'result_backend',
            'CELERY_TASK_SERIALIZER': 'task_serializer',
            'CELERY_RESULT_SERIALIZER': 'result_serializer',
            'CELERY_ACCEPT_CONTENT': 'accept_content',
            'CELERY_TIMEZONE': 'timezone',
            'CELERY_ENABLE_UTC': 'enable_utc',
            'CELERY_TASK_ACKS_LATE': 'task_acks_late',
            'CELERY_WORKER_PREFETCH_MULTIPLIER': 'worker_prefetch_multiplier',
            'CELERY_TASK_REJECT_ON_WORKER_LOST': 'task_reject_on_worker_lost',
        }
        
        # Convert Flask config keys to Celery 5.x format
        for flask_key, celery_key in config_mapping.items():
            if flask_key in app.config:
                celery_config[celery_key] = app.config[flask_key]
        
        # Update Celery config with converted values
        # This will override the default broker/backend if Flask config
        # provides different values (e.g., from environment variables)
        if celery_config:
            celery.conf.update(celery_config)
        
        # CRITICAL: Remove old CELERY_* keys from Flask config to prevent
        # Celery from detecting mixed old/new configuration keys.
        # Celery 5.x's detect_settings() scans Flask config and will raise
        # ImproperlyConfigured if it finds old-style keys.
        for flask_key in config_mapping.keys():
            if flask_key in app.config:
                del app.config[flask_key]
        
        # Store Flask app reference for use in tasks that need app context
        celery.app = app
    
    return celery
