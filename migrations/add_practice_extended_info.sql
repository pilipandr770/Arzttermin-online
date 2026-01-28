-- Migration: Add extended information fields to practices table
-- Date: 2026-01-29
-- Description: Add website, google_business_url, description, opening_hours, social_media, photos

-- Add new columns
ALTER TABLE terminfinder.practices 
ADD COLUMN IF NOT EXISTS website VARCHAR(500),
ADD COLUMN IF NOT EXISTS google_business_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS opening_hours TEXT,
ADD COLUMN IF NOT EXISTS social_media TEXT,
ADD COLUMN IF NOT EXISTS photos TEXT;

-- Add comments for documentation
COMMENT ON COLUMN terminfinder.practices.website IS 'Practice website URL';
COMMENT ON COLUMN terminfinder.practices.google_business_url IS 'Google Business profile URL';
COMMENT ON COLUMN terminfinder.practices.description IS 'Practice description for patients';
COMMENT ON COLUMN terminfinder.practices.opening_hours IS 'JSON: Opening hours by day of week';
COMMENT ON COLUMN terminfinder.practices.social_media IS 'JSON: Social media links (facebook, instagram, etc)';
COMMENT ON COLUMN terminfinder.practices.photos IS 'JSON: Array of photo URLs';
