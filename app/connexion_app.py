"""Connexion application factory for Swagger/OpenAPI support."""
import logging
import os
import connexion
from connexion import FlaskApp
from flask import Flask
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file early
# This ensures .env is loaded before any config classes are imported
load_dotenv()


def create_connexion_app(config_name: str = "development", skip_db_init: bool = False) -> FlaskApp:
    """Create a Connexion application with Flask backend.
    
    Args:
        config_name: Configuration environment name.
                    Options: "development", "production", "testing"
        skip_db_init: If True, skip database table creation (useful for migrations)
    
    Returns:
        Connexion FlaskApp instance
    """
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    openapi_dir = os.path.join(project_root, "openapi")
    openapi_spec = os.path.join(openapi_dir, "openapi.yaml")
    
    # Verify OpenAPI file exists
    if not os.path.exists(openapi_spec):
        raise FileNotFoundError(f"OpenAPI specification not found: {openapi_spec}")
    
    # Create Connexion app with specification directory
    # Load config first, then create app with config
    if config_name == "production":
        from app.config import ProductionConfig
        ProductionConfig.validate()
        config_obj = ProductionConfig
    elif config_name == "testing":
        from app.config import TestingConfig
        config_obj = TestingConfig
    else:
        from app.config import DevelopmentConfig
        config_obj = DevelopmentConfig
    
    # Create Connexion app
    # According to Connexion 3.x docs, we can create the app and add API
    connexion_app = FlaskApp(__name__, specification_dir=openapi_dir)
    
    # Get the underlying Flask app to configure it
    app = connexion_app.app
    
    # Load configuration FIRST before adding API
    app.config.from_object(config_obj)
    
    # Ensure database directory exists for SQLite
    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite:///"):
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        if db_path != ":memory:":
            if not os.path.isabs(db_path):
                db_path = os.path.join(project_root, db_path)
            db_path = os.path.normpath(db_path)
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            db_uri_path = db_path.replace("\\", "/")
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_uri_path}"
    
    # Initialize extensions with app BEFORE adding API
    # Import here to avoid circular imports
    from app import db, cache
    db.init_app(app)
    cache.init_app(app)
    
    # Initialize Celery with app
    from app.celery_app import init_celery
    init_celery(app)
    
    # Add API specification AFTER configuring Flask app
    # Use RelativeResolver for Connexion 3.x and our modular controller layout
    resolver = connexion.resolver.RelativeResolver("app.api.v1")
    
    try:
        # Add API with base_path - paths in openapi.yaml are relative to base_path
        api = connexion_app.add_api(
            "openapi.yaml",
            base_path="/api",
            validate_responses=False,  # Set to False initially for debugging
            strict_validation=False,   # Set to False initially for debugging
            pythonic_params=True,
            resolver=resolver
        )
        logger.info(f"API specification added successfully")
    except Exception as e:
        logger.error(f"Failed to add API specification: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise
    
    
    # Log registered routes for debugging
    with app.app_context():
        routes = list(app.url_map.iter_rules())
        logger.info(f"Total routes registered: {len(routes)}")
        for rule in routes[:20]:  # Log first 20 routes
            logger.info(f"Route: {rule.rule} -> {rule.endpoint}")
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        from flask import jsonify
        return jsonify({"error": "Resource not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import jsonify
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
    
    # Create database tables only in development/testing
    if not skip_db_init and config_name in ("development", "testing"):
        with app.app_context():
            db.create_all()
    
    return connexion_app

