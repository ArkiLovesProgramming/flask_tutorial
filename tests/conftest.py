"""Shared pytest fixtures."""
import pytest

from app import db
from app.connexion_app import create_connexion_app
from app.models import User
from app.services.auth_service import AuthService


@pytest.fixture(scope="session")
def connexion_app():
    """Create the Connexion ASGI app configured for testing."""
    cnx_app = create_connexion_app("testing")
    app = cnx_app.app

    with app.app_context():
        db.create_all()
    yield cnx_app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(connexion_app):
    """Provide a Connexion test client with an isolated database."""
    app = connexion_app.app

    with app.app_context():
        db.drop_all()
        db.create_all()

    test_client = connexion_app.test_client()
    test_client.application = app
    yield test_client

    with app.app_context():
        db.session.remove()


@pytest.fixture
def test_user(client):
    """Create a test user for authentication tests."""
    with client.application.app_context():
        # Clean up any existing test user first
        existing = User.query.filter_by(username="testuser").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        # Create a user with password
        password_hash = AuthService.hash_password("testpassword123")
        user = User(username="testuser", email="test@example.com", password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        yield user
        
        # Cleanup
        db.session.delete(user)
        db.session.commit()
