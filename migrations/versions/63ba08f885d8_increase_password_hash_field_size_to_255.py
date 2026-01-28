"""Increase password_hash field size to 255

Revision ID: 63ba08f885d8
Revises: be41b2616706
Create Date: 2026-01-28 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63ba08f885d8'
down_revision = 'be41b2616706'
branch_labels = None
depends_on = None


def upgrade():
    # Change password_hash field size from 128 to 255
    op.alter_column('doctors', 'password_hash',
                    existing_type=sa.String(128),
                    type_=sa.String(255),
                    existing_nullable=False,
                    schema='terminfinder')


def downgrade():
    # Revert password_hash field size back to 128
    op.alter_column('doctors', 'password_hash',
                    existing_type=sa.String(255),
                    type_=sa.String(128),
                    existing_nullable=False,
                    schema='terminfinder')
