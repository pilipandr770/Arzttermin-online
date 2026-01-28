"""Initial migration for PostgreSQL deployment

Revision ID: be41b2616706
Revises: 
Create Date: 2026-01-28 20:00:44.385325

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be41b2616706'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create schema if it doesn't exist
    op.execute('CREATE SCHEMA IF NOT EXISTS terminfinder')
    
    # Create practices table
    op.create_table('practices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('vat_number', sa.String(length=20), nullable=True),
        sa.Column('handelsregister_nr', sa.String(length=50), nullable=True),
        sa.Column('owner_email', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('total_appointments', sa.Integer(), nullable=False),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        schema='terminfinder'
    )
    op.create_primary_key('practices_pkey', 'practices', ['id'], schema='terminfinder')
    op.create_index('ix_practices_owner_email', 'practices', ['owner_email'], schema='terminfinder')
    
    # Create doctors table
    op.create_table('doctors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('practice_id', sa.UUID(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=True),
        sa.Column('tax_number', sa.String(length=50), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('verification_token', sa.String(length=100), nullable=True),
        sa.Column('speciality', sa.String(length=50), nullable=True),
        sa.Column('speciality_custom', sa.String(length=100), nullable=True),
        sa.Column('speciality_approved', sa.Boolean(), nullable=True),
        sa.Column('languages', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('slot_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('work_days', sa.Text(), nullable=True),
        sa.Column('work_start_time', sa.Time(), nullable=True),
        sa.Column('work_end_time', sa.Time(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        schema='terminfinder'
    )
    op.create_primary_key('doctors_pkey', 'doctors', ['id'], schema='terminfinder')
    op.create_index('ix_doctors_email', 'doctors', ['email'], schema='terminfinder')
    op.create_index('ix_doctors_practice_id', 'doctors', ['practice_id'], schema='terminfinder')
    op.create_foreign_key('doctors_practice_id_fkey', 'doctors', 'practices', ['practice_id'], ['id'], source_schema='terminfinder', referent_schema='terminfinder')
    
    # Create patients table
    op.create_table('patients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=True),
        sa.Column('total_bookings', sa.Integer(), nullable=False),
        sa.Column('no_show_count', sa.Integer(), nullable=False),
        sa.Column('late_cancellations', sa.Integer(), nullable=False),
        sa.Column('early_cancellations', sa.Integer(), nullable=False),
        sa.Column('attended_appointments', sa.Integer(), nullable=False),
        sa.Column('notification_email', sa.Boolean(), nullable=False),
        sa.Column('notification_sms', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        schema='terminfinder'
    )
    op.create_primary_key('patients_pkey', 'patients', ['id'], schema='terminfinder')
    op.create_index('ix_patients_phone', 'patients', ['phone'], schema='terminfinder')
    op.create_index('ix_patients_stripe_customer_id', 'patients', ['stripe_customer_id'], schema='terminfinder')
    
    # Create calendars table
    op.create_table('calendars',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('working_hours', sa.Text(), nullable=True),
        sa.Column('slot_duration', sa.Integer(), nullable=False),
        sa.Column('buffer_time', sa.Integer(), nullable=False),
        sa.Column('max_advance_booking_days', sa.Integer(), nullable=False),
        sa.Column('min_advance_booking_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        schema='terminfinder'
    )
    op.create_primary_key('calendars_pkey', 'calendars', ['id'], schema='terminfinder')
    op.create_index('ix_calendars_doctor_id', 'calendars', ['doctor_id'], schema='terminfinder')
    op.create_foreign_key('calendars_doctor_id_fkey', 'calendars', 'doctors', ['doctor_id'], ['id'], source_schema='terminfinder', referent_schema='terminfinder')
    
    # Create time_slots table
    op.create_table('time_slots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('calendar_id', sa.UUID(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('block_reason', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        schema='terminfinder'
    )
    op.create_primary_key('time_slots_pkey', 'time_slots', ['id'], schema='terminfinder')
    op.create_index('ix_time_slots_calendar_id', 'time_slots', ['calendar_id'], schema='terminfinder')
    op.create_index('ix_time_slots_start_time', 'time_slots', ['start_time'], schema='terminfinder')
    op.create_index('ix_time_slots_status', 'time_slots', ['status'], schema='terminfinder')
    op.create_foreign_key('time_slots_calendar_id_fkey', 'time_slots', 'calendars', ['calendar_id'], ['id'], source_schema='terminfinder', referent_schema='terminfinder')
    
    # Create bookings table
    op.create_table('bookings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('timeslot_id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('payment_intent_id', sa.String(length=100), nullable=False),
        sa.Column('amount_paid', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('refund_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('booking_code', sa.String(length=8), nullable=False),
        sa.Column('cancellable_until', sa.DateTime(), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.String(length=20), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('attended', sa.Boolean(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=False),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        schema='terminfinder'
    )
    op.create_primary_key('bookings_pkey', 'bookings', ['id'], schema='terminfinder')
    op.create_index('ix_bookings_booking_code', 'bookings', ['booking_code'], schema='terminfinder')
    op.create_index('ix_bookings_patient_id', 'bookings', ['patient_id'], schema='terminfinder')
    op.create_index('ix_bookings_payment_intent_id', 'bookings', ['payment_intent_id'], schema='terminfinder')
    op.create_index('ix_bookings_status', 'bookings', ['status'], schema='terminfinder')
    op.create_index('ix_bookings_timeslot_id', 'bookings', ['timeslot_id'], schema='terminfinder')
    op.create_foreign_key('bookings_timeslot_id_fkey', 'bookings', 'time_slots', ['timeslot_id'], ['id'], source_schema='terminfinder', referent_schema='terminfinder')
    op.create_foreign_key('bookings_patient_id_fkey', 'bookings', 'patients', ['patient_id'], ['id'], source_schema='terminfinder', referent_schema='terminfinder')
    
    # Create patient_alerts table
    op.create_table('patient_alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('search_criteria', sa.JSON(), nullable=False),
        sa.Column('email_notifications', sa.Boolean(), nullable=False),
        sa.Column('sms_notifications', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notifications_sent', sa.Integer(), nullable=False),
        sa.Column('last_notification_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        schema='terminfinder'
    )
    op.create_primary_key('patient_alerts_pkey', 'patient_alerts', ['id'], schema='terminfinder')
    op.create_index('ix_patient_alerts_patient_id', 'patient_alerts', ['patient_id'], schema='terminfinder')
    op.create_foreign_key('patient_alerts_patient_id_fkey', 'patient_alerts', 'patients', ['patient_id'], ['id'], source_schema='terminfinder', referent_schema='terminfinder')


def downgrade():
    # Drop tables in reverse order
    op.drop_table('patient_alerts', schema='terminfinder')
    op.drop_table('bookings', schema='terminfinder')
    op.drop_table('time_slots', schema='terminfinder')
    op.drop_table('calendars', schema='terminfinder')
    op.drop_table('patients', schema='terminfinder')
    op.drop_table('doctors', schema='terminfinder')
    op.drop_table('practices', schema='terminfinder')
    
    # Drop schema
    op.execute('DROP SCHEMA IF EXISTS terminfinder CASCADE')
