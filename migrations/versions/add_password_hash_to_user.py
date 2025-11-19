"""Add password_hash to user table

Revision ID: add_password_hash
Revises: ddd2e1fb1067
Create Date: 2025-11-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_password_hash'
down_revision = 'ddd2e1fb1067'
branch_labels = None
depends_on = None


def upgrade():
    # Add password_hash column to user table
    op.add_column('user', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade():
    # Remove password_hash column from user table
    op.drop_column('user', 'password_hash')

