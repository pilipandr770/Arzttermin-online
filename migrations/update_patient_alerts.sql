-- Migration: Update patient_alerts table structure
-- Date: 2026-01-29
-- Description: Replace JSON search_criteria with specific fields for doctor alerts

-- Drop old column
ALTER TABLE terminfinder.patient_alerts 
DROP COLUMN IF EXISTS search_criteria;

-- Add new columns
ALTER TABLE terminfinder.patient_alerts 
ADD COLUMN IF NOT EXISTS doctor_id UUID REFERENCES terminfinder.doctors(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS speciality VARCHAR(50),
ADD COLUMN IF NOT EXISTS city VARCHAR(100),
ADD COLUMN IF NOT EXISTS date_from DATE,
ADD COLUMN IF NOT EXISTS date_to DATE,
ADD COLUMN IF NOT EXISTS last_slot_notified_id UUID;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_patient_alerts_doctor ON terminfinder.patient_alerts(doctor_id);
CREATE INDEX IF NOT EXISTS idx_patient_alerts_speciality ON terminfinder.patient_alerts(speciality);
CREATE INDEX IF NOT EXISTS idx_patient_alerts_active ON terminfinder.patient_alerts(is_active);

-- Add comments
COMMENT ON COLUMN terminfinder.patient_alerts.doctor_id IS 'Specific doctor to get alerts for';
COMMENT ON COLUMN terminfinder.patient_alerts.speciality IS 'Speciality filter if doctor_id not specified';
COMMENT ON COLUMN terminfinder.patient_alerts.city IS 'City filter';
COMMENT ON COLUMN terminfinder.patient_alerts.date_from IS 'Desired date range start';
COMMENT ON COLUMN terminfinder.patient_alerts.date_to IS 'Desired date range end';
COMMENT ON COLUMN terminfinder.patient_alerts.last_slot_notified_id IS 'Last slot that triggered notification (prevent duplicates)';
