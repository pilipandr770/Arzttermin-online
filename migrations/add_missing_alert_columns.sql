-- Migration: Add missing columns to patient_alerts
-- Date: 2026-01-29
-- Description: Add last_notification_at, notifications_sent, email_notifications, sms_notifications

-- Add missing timestamp column
ALTER TABLE terminfinder.patient_alerts 
ADD COLUMN IF NOT EXISTS last_notification_at TIMESTAMP;

-- Add notification settings if missing
ALTER TABLE terminfinder.patient_alerts 
ADD COLUMN IF NOT EXISTS notifications_sent INTEGER DEFAULT 0;

ALTER TABLE terminfinder.patient_alerts 
ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE;

ALTER TABLE terminfinder.patient_alerts 
ADD COLUMN IF NOT EXISTS sms_notifications BOOLEAN DEFAULT FALSE;

-- Add comments
COMMENT ON COLUMN terminfinder.patient_alerts.last_notification_at IS 'Timestamp of last notification sent';
COMMENT ON COLUMN terminfinder.patient_alerts.notifications_sent IS 'Count of notifications sent for this alert';
COMMENT ON COLUMN terminfinder.patient_alerts.email_notifications IS 'Enable email notifications';
COMMENT ON COLUMN terminfinder.patient_alerts.sms_notifications IS 'Enable SMS notifications (future feature)';
