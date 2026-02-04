"""Create admin table

Revision ID: create_admin_table
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os

# revision identifiers, used by Alembic.
revision = 'create_admin_table'
down_revision = '07_add_chatbot_instructions'
branch_labels = None
depends_on = None

# Get schema from environment
schema = os.getenv('DB_SCHEMA', 'public')


def upgrade():
    # Create admins table
    op.create_table('admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('two_factor_secret', sa.String(length=32), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('account_locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        schema=schema
    )
    op.create_index(op.f('ix_admins_email'), 'admins', ['email'], unique=True, schema=schema)
    op.create_index(op.f('ix_admins_username'), 'admins', ['username'], unique=True, schema=schema)


def downgrade():
    op.drop_index(op.f('ix_admins_username'), table_name='admins', schema=schema)
    op.drop_index(op.f('ix_admins_email'), table_name='admins', schema=schema)
    op.drop_table('admins', schema=schema)
