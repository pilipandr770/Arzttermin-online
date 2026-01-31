"""add chatbot instructions to practice

Revision ID: 07_add_chatbot_instructions
Revises: 06_add_extended_profiles
Create Date: 2026-01-31 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '07_add_chatbot_instructions'
down_revision = '06_add_extended_profiles'
branch_labels = None
depends_on = None


def upgrade():
    """Добавляем поле chatbot_instructions для кастомизации AI ассистента практики"""
    
    # Определяем схему из переменной окружения или используем public
    import os
    schema = os.getenv('DB_SCHEMA', 'public')
    
    # Добавляем поле chatbot_instructions
    op.add_column(
        'practices',
        sa.Column('chatbot_instructions', sa.Text(), nullable=True),
        schema=schema
    )
    
    print(f"✅ Added chatbot_instructions to {schema}.practices")


def downgrade():
    """Откатываем изменения"""
    import os
    schema = os.getenv('DB_SCHEMA', 'public')
    
    op.drop_column('practices', 'chatbot_instructions', schema=schema)
    
    print(f"✅ Removed chatbot_instructions from {schema}.practices")
