"""Add practice extended fields and patient_alerts restructure

Revision ID: 04_practice_alerts
Revises: 9ef6c9f1ee44
Create Date: 2026-01-29 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '04_practice_alerts'
down_revision = '9ef6c9f1ee44'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection to check if columns exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns for practices table
    practices_columns = [col['name'] for col in inspector.get_columns('practices', schema='terminfinder')]
    
    # Add new fields to practices table only if they don't exist
    if 'website' not in practices_columns:
        op.add_column('practices', sa.Column('website', sa.String(length=500), nullable=True), schema='terminfinder')
    if 'google_business_url' not in practices_columns:
        op.add_column('practices', sa.Column('google_business_url', sa.String(length=500), nullable=True), schema='terminfinder')
    if 'description' not in practices_columns:
        op.add_column('practices', sa.Column('description', sa.Text(), nullable=True), schema='terminfinder')
    if 'opening_hours' not in practices_columns:
        op.add_column('practices', sa.Column('opening_hours', sa.Text(), nullable=True), schema='terminfinder')
    if 'social_media' not in practices_columns:
        op.add_column('practices', sa.Column('social_media', sa.Text(), nullable=True), schema='terminfinder')
    if 'photos' not in practices_columns:
        op.add_column('practices', sa.Column('photos', sa.Text(), nullable=True), schema='terminfinder')
    
    # Get existing columns for patient_alerts table
    alerts_columns = [col['name'] for col in inspector.get_columns('patient_alerts', schema='terminfinder')]
    
    # Drop old column if exists
    if 'search_criteria' in alerts_columns:
        op.drop_column('patient_alerts', 'search_criteria', schema='terminfinder')
    
    # Add new columns to patient_alerts only if they don't exist
    if 'doctor_id' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=True), schema='terminfinder')
    if 'speciality' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('speciality', sa.String(length=50), nullable=True), schema='terminfinder')
    if 'city' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('city', sa.String(length=100), nullable=True), schema='terminfinder')
    if 'date_from' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('date_from', sa.Date(), nullable=True), schema='terminfinder')
    if 'date_to' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('date_to', sa.Date(), nullable=True), schema='terminfinder')
    if 'email_notifications' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('email_notifications', sa.Boolean(), nullable=True, server_default='true'), schema='terminfinder')
    if 'sms_notifications' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('sms_notifications', sa.Boolean(), nullable=True, server_default='false'), schema='terminfinder')
    if 'notifications_sent' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('notifications_sent', sa.Integer(), nullable=True, server_default='0'), schema='terminfinder')
    if 'last_notification_at' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('last_notification_at', sa.DateTime(), nullable=True), schema='terminfinder')
    if 'last_slot_notified_id' not in alerts_columns:
        op.add_column('patient_alerts', sa.Column('last_slot_notified_id', postgresql.UUID(as_uuid=True), nullable=True), schema='terminfinder')
    
    # Get existing indexes
    indexes = [idx['name'] for idx in inspector.get_indexes('patient_alerts', schema='terminfinder')]
    
    # Create indexes only if they don't exist
    if 'ix_terminfinder_patient_alerts_doctor_id' not in indexes:
        op.create_index('ix_terminfinder_patient_alerts_doctor_id', 'patient_alerts', ['doctor_id'], unique=False, schema='terminfinder')
    if 'ix_terminfinder_patient_alerts_speciality' not in indexes:
        op.create_index('ix_terminfinder_patient_alerts_speciality', 'patient_alerts', ['speciality'], unique=False, schema='terminfinder')
    if 'ix_terminfinder_patient_alerts_is_active' not in indexes:
        op.create_index('ix_terminfinder_patient_alerts_is_active', 'patient_alerts', ['is_active'], unique=False, schema='terminfinder')
    
    # Get existing foreign keys
    fks = [fk['name'] for fk in inspector.get_foreign_keys('patient_alerts', schema='terminfinder')]
    
    # Create foreign key only if it doesn't exist
    if 'fk_patient_alerts_doctor_id' not in fks and 'doctor_id' in alerts_columns:
        try:
            op.create_foreign_key(
                'fk_patient_alerts_doctor_id',
                'patient_alerts', 'doctors',
                ['doctor_id'], ['id'],
                source_schema='terminfinder',
                referent_schema='terminfinder',
                ondelete='CASCADE'
            )
        except:
            pass  # Foreign key might already exist with different name


def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_patient_alerts_doctor_id', 'patient_alerts', schema='terminfinder', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_terminfinder_patient_alerts_is_active', table_name='patient_alerts', schema='terminfinder')
    op.drop_index('ix_terminfinder_patient_alerts_speciality', table_name='patient_alerts', schema='terminfinder')
    op.drop_index('ix_terminfinder_patient_alerts_doctor_id', table_name='patient_alerts', schema='terminfinder')
    
    # Drop patient_alerts columns
    op.drop_column('patient_alerts', 'last_slot_notified_id', schema='terminfinder')
    op.drop_column('patient_alerts', 'last_notification_at', schema='terminfinder')
    op.drop_column('patient_alerts', 'notifications_sent', schema='terminfinder')
    op.drop_column('patient_alerts', 'sms_notifications', schema='terminfinder')
    op.drop_column('patient_alerts', 'email_notifications', schema='terminfinder')
    op.drop_column('patient_alerts', 'date_to', schema='terminfinder')
    op.drop_column('patient_alerts', 'date_from', schema='terminfinder')
    op.drop_column('patient_alerts', 'city', schema='terminfinder')
    op.drop_column('patient_alerts', 'speciality', schema='terminfinder')
    op.drop_column('patient_alerts', 'doctor_id', schema='terminfinder')
    
    # Drop practices columns
    op.drop_column('practices', 'photos', schema='terminfinder')
    op.drop_column('practices', 'social_media', schema='terminfinder')
    op.drop_column('practices', 'opening_hours', schema='terminfinder')
    op.drop_column('practices', 'description', schema='terminfinder')
    op.drop_column('practices', 'google_business_url', schema='terminfinder')
    op.drop_column('practices', 'website', schema='terminfinder')
