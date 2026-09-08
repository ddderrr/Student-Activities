-- Run this ONCE on the existing PostgreSQL database.
-- create_all() does not add columns to tables that already exist.

ALTER TABLE activities
ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';

UPDATE activities
SET status = 'active'
WHERE status IS NULL;
