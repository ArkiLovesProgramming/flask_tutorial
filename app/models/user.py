"""User SQLAlchemy model."""
from app import db


class User(db.Model):
    """User model for storing user data."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    # Role: 'user' or 'admin'
    role = db.Column(db.String(20), default='user', nullable=False)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
