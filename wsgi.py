"""Entry point for running the Flask application with Connexion and Swagger UI.

Development:
    python wsgi.py

Production (using uvicorn):
    uvicorn wsgi:app --host 0.0.0.0 --port 5000

Production (using gunicorn with uvicorn workers):
    gunicorn wsgi:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000

Swagger UI is available at: http://localhost:5000/api/ui
"""
import os
from dotenv import load_dotenv
from app.connexion_app import create_connexion_app

# Load environment variables from .env file
# This will not override existing environment variables
load_dotenv()

# Create the Connexion app instance
# This will be used by both development and production
env = os.getenv("FLASK_ENV", "development")
connexion_app = create_connexion_app(env)

# For WSGI/ASGI servers, expose the Connexion app itself
# The middleware will handle routing
app = connexion_app

if __name__ == "__main__":
    # Development mode: use connexion_app.run() with import string for reload
    print("Starting Flask application with Connexion (Development Mode)")
    print("Swagger UI available at: http://localhost:5000/api/ui")
    # Pass as import string to enable reload functionality
    connexion_app.run(
        import_string="wsgi:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
