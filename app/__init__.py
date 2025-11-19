"""Application core module.

This module provides shared resources (db, cache) that are used across the application.
The actual application factory is in app.connexion_app.
"""
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

# Initialize extensions without binding to app (deferred initialization)
# These are shared resources used by the Connexion app
db = SQLAlchemy()
cache = Cache()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
