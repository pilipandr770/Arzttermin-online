"""Add calendar integrations support

Revision ID: 05_add_calendar_integrations
Revises: 04_practice_alerts
Create Date: 2026-01-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '05_add_calendar_integrations'
down_revision = '04_practice_alerts'
branch_labels = None
depends_on = None


def upgrade():
    # Создать таблицу calendar_integrations
    op.create_table(
        'calendar_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('terminfinder.doctors.id'), nullable=False, index=True),
        
        # Тип провайдера
        sa.Column('provider', sa.String(20), nullable=False),
        
        # OAuth 2.0 Credentials
        sa.Column('oauth_access_token', sa.Text, nullable=True),
        sa.Column('oauth_refresh_token', sa.Text, nullable=True),
        sa.Column('oauth_token_expires_at', sa.DateTime, nullable=True),
        sa.Column('oauth_scope', sa.String(500), nullable=True),
        
        # CalDAV Credentials
        sa.Column('caldav_url', sa.String(500), nullable=True),
        sa.Column('caldav_username', sa.String(200), nullable=True),
        sa.Column('caldav_password', sa.Text, nullable=True),
        sa.Column('caldav_calendar_id', sa.String(200), nullable=True),
        
        # Настройки синхронизации
        sa.Column('sync_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('sync_direction', sa.String(20), default='both', nullable=False),
        
        # Статус синхронизации
        sa.Column('last_sync_at', sa.DateTime, nullable=True),
        sa.Column('next_sync_at', sa.DateTime, nullable=True),
        sa.Column('sync_status', sa.String(20), default='active', nullable=False),
        sa.Column('sync_error_message', sa.Text, nullable=True),
        sa.Column('sync_error_count', sa.Integer, default=0, nullable=False),
        
        # Webhook Configuration
        sa.Column('external_webhook_id', sa.String(200), nullable=True),
        sa.Column('external_resource_id', sa.String(200), nullable=True),
        sa.Column('webhook_expires_at', sa.DateTime, nullable=True),
        
        # Настройки создания событий
        sa.Column('event_title_template', sa.String(200), default='Termin mit {patient_name}', nullable=False),
        sa.Column('event_description_template', sa.Text, default='Patient: {patient_name}\nTelefon: {patient_phone}', nullable=False),
        sa.Column('event_color_id', sa.String(10), nullable=True),
        sa.Column('event_reminders', sa.Boolean, default=True, nullable=False),
        
        # Настройки блокировки слотов
        sa.Column('import_free_busy', sa.Boolean, default=True, nullable=False),
        sa.Column('import_event_titles', sa.Boolean, default=False, nullable=False),
        sa.Column('auto_block_conflicts', sa.Boolean, default=True, nullable=False),
        
        # Дополнительные метаданные
        sa.Column('external_calendar_name', sa.String(200), nullable=True),
        sa.Column('external_calendar_timezone', sa.String(50), default='Europe/Berlin', nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('connected_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('disconnected_at', sa.DateTime, nullable=True),
        
        schema='terminfinder'
    )
    
    # Создать индекс для быстрого поиска интеграций врача
    op.create_index(
        'ix_calendar_integrations_doctor_provider',
        'calendar_integrations',
        ['doctor_id', 'provider'],
        unique=True,
        schema='terminfinder'
    )
    
    # Создать индекс для поиска по webhook_id
    op.create_index(
        'ix_calendar_integrations_webhook_id',
        'calendar_integrations',
        ['external_webhook_id'],
        schema='terminfinder'
    )


def downgrade():
    # Удалить индексы
    op.drop_index('ix_calendar_integrations_webhook_id', table_name='calendar_integrations', schema='terminfinder')
    op.drop_index('ix_calendar_integrations_doctor_provider', table_name='calendar_integrations', schema='terminfinder')
    
    # Удалить таблицу
    op.drop_table('calendar_integrations', schema='terminfinder')
