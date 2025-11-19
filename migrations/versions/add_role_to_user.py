"""Add role column to user table

Revision ID: add_role_to_user
Revises: add_password_hash
Create Date: 2025-11-19 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_role_to_user'
down_revision = 'add_password_hash'
branch_labels = None
depends_on = None


def upgrade():
    # Add role column to user table with default value 'user'
    op.add_column('user', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))


def downgrade():
    # Remove role column from user table
    op.drop_column('user', 'role')

