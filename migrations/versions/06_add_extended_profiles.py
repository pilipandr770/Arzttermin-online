"""
06: Add extended profile fields and reviews

Revision ID: 06_add_extended_profiles
Revises: 05_add_calendar_integrations
Create Date: 2024-01-XX
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '06_add_extended_profiles'
down_revision = '05_add_calendar_integrations'
branch_labels = None
depends_on = None


def upgrade():
    # === Practice table extensions ===
    op.add_column('practices', sa.Column('gallery_photos', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('video_url', sa.String(length=500), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('virtual_tour_url', sa.String(length=500), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('services', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('team_members', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('equipment', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('accepted_insurances', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('features', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('certifications', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('faq', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('rating_avg', sa.Float(), nullable=True, server_default='0.0'), schema='terminfinder')
    op.add_column('practices', sa.Column('rating_count', sa.Integer(), nullable=True, server_default='0'), schema='terminfinder')
    op.add_column('practices', sa.Column('parking_info', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('public_transport', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('emergency_phone', sa.String(length=20), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('whatsapp_number', sa.String(length=20), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('telegram_username', sa.String(length=100), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('meta_title', sa.String(length=200), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('meta_description', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('practices', sa.Column('slug', sa.String(length=200), nullable=True), schema='terminfinder')
    
    # Create index for slug
    op.create_index(op.f('ix_terminfinder_practices_slug'), 'practices', ['slug'], unique=True, schema='terminfinder')
    
    # === Doctor table extensions ===
    op.add_column('doctors', sa.Column('title', sa.String(length=50), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('qualifications', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('experience_years', sa.Integer(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('previous_positions', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('treatment_focus', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('subspecialities', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('professional_memberships', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('publications', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('consultation_types', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('video_consultation_url', sa.String(length=500), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('hobbies', sa.Text(), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('motto', sa.String(length=500), nullable=True), schema='terminfinder')
    op.add_column('doctors', sa.Column('preferred_contact_method', sa.String(length=20), nullable=True), schema='terminfinder')
    
    # === Create practice_reviews table ===
    op.create_table(
        'practice_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('practice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Ratings
        sa.Column('rating_overall', sa.Integer(), nullable=False),
        sa.Column('rating_treatment', sa.Integer(), nullable=True),
        sa.Column('rating_staff', sa.Integer(), nullable=True),
        sa.Column('rating_facilities', sa.Integer(), nullable=True),
        sa.Column('rating_waiting_time', sa.Integer(), nullable=True),
        
        # Review content
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        
        # Meta
        sa.Column('visit_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        
        # Status and moderation
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('flagged_reason', sa.String(length=500), nullable=True),
        
        # Practice response
        sa.Column('practice_response', sa.Text(), nullable=True),
        sa.Column('practice_response_at', sa.DateTime(), nullable=True),
        sa.Column('practice_response_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Helpfulness
        sa.Column('helpful_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('not_helpful_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['practice_id'], ['terminfinder.practices.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['terminfinder.patients.id'], ),
        sa.ForeignKeyConstraint(['doctor_id'], ['terminfinder.doctors.id'], ),
        sa.ForeignKeyConstraint(['booking_id'], ['terminfinder.bookings.id'], ),
        
        schema='terminfinder'
    )
    
    # Create indexes for practice_reviews
    op.create_index(op.f('ix_terminfinder_practice_reviews_practice_id'), 'practice_reviews', ['practice_id'], schema='terminfinder')
    op.create_index(op.f('ix_terminfinder_practice_reviews_patient_id'), 'practice_reviews', ['patient_id'], schema='terminfinder')
    op.create_index(op.f('ix_terminfinder_practice_reviews_doctor_id'), 'practice_reviews', ['doctor_id'], schema='terminfinder')
    op.create_index(op.f('ix_terminfinder_practice_reviews_is_published'), 'practice_reviews', ['is_published'], schema='terminfinder')
    op.create_index(op.f('ix_terminfinder_practice_reviews_created_at'), 'practice_reviews', ['created_at'], schema='terminfinder')


def downgrade():
    # Drop practice_reviews table and indexes
    op.drop_index(op.f('ix_terminfinder_practice_reviews_created_at'), table_name='practice_reviews', schema='terminfinder')
    op.drop_index(op.f('ix_terminfinder_practice_reviews_is_published'), table_name='practice_reviews', schema='terminfinder')
    op.drop_index(op.f('ix_terminfinder_practice_reviews_doctor_id'), table_name='practice_reviews', schema='terminfinder')
    op.drop_index(op.f('ix_terminfinder_practice_reviews_patient_id'), table_name='practice_reviews', schema='terminfinder')
    op.drop_index(op.f('ix_terminfinder_practice_reviews_practice_id'), table_name='practice_reviews', schema='terminfinder')
    op.drop_table('practice_reviews', schema='terminfinder')
    
    # Drop doctor columns
    op.drop_column('doctors', 'preferred_contact_method', schema='terminfinder')
    op.drop_column('doctors', 'motto', schema='terminfinder')
    op.drop_column('doctors', 'hobbies', schema='terminfinder')
    op.drop_column('doctors', 'video_consultation_url', schema='terminfinder')
    op.drop_column('doctors', 'consultation_types', schema='terminfinder')
    op.drop_column('doctors', 'publications', schema='terminfinder')
    op.drop_column('doctors', 'professional_memberships', schema='terminfinder')
    op.drop_column('doctors', 'subspecialities', schema='terminfinder')
    op.drop_column('doctors', 'treatment_focus', schema='terminfinder')
    op.drop_column('doctors', 'previous_positions', schema='terminfinder')
    op.drop_column('doctors', 'experience_years', schema='terminfinder')
    op.drop_column('doctors', 'qualifications', schema='terminfinder')
    op.drop_column('doctors', 'title', schema='terminfinder')
    
    # Drop practice columns and index
    op.drop_index(op.f('ix_terminfinder_practices_slug'), table_name='practices', schema='terminfinder')
    op.drop_column('practices', 'slug', schema='terminfinder')
    op.drop_column('practices', 'meta_description', schema='terminfinder')
    op.drop_column('practices', 'meta_title', schema='terminfinder')
    op.drop_column('practices', 'telegram_username', schema='terminfinder')
    op.drop_column('practices', 'whatsapp_number', schema='terminfinder')
    op.drop_column('practices', 'emergency_phone', schema='terminfinder')
    op.drop_column('practices', 'public_transport', schema='terminfinder')
    op.drop_column('practices', 'parking_info', schema='terminfinder')
    op.drop_column('practices', 'rating_count', schema='terminfinder')
    op.drop_column('practices', 'rating_avg', schema='terminfinder')
    op.drop_column('practices', 'faq', schema='terminfinder')
    op.drop_column('practices', 'certifications', schema='terminfinder')
    op.drop_column('practices', 'features', schema='terminfinder')
    op.drop_column('practices', 'accepted_insurances', schema='terminfinder')
    op.drop_column('practices', 'equipment', schema='terminfinder')
    op.drop_column('practices', 'team_members', schema='terminfinder')
    op.drop_column('practices', 'services', schema='terminfinder')
    op.drop_column('practices', 'virtual_tour_url', schema='terminfinder')
    op.drop_column('practices', 'video_url', schema='terminfinder')
    op.drop_column('practices', 'gallery_photos', schema='terminfinder')
