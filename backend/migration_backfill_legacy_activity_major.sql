-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
--
-- migration_add_activity_major.sql set activities.major = NULL for every row
-- that existed before the column was added (5 rows on this DB: ids 5-9),
-- which made them "unowned" and visible to every branch admin.
--
-- On inspection, 4 of those 5 rows have department text that clearly
-- identifies them as Computer Science activities (typos and all):
--   id 5  department = 'Computer Sciecne'
--   id 6  department = 'Computer Science'
--   id 7  department = 'Computer Building'
--   id 8  department = 'Com'
-- Backfill those 4 to the CS major so Chemistry admins stop seeing them.
--
-- id 9 (department = 'ปปกป', name = 'กสสกวแกแก') is keyboard-mash test data
-- with no signal for either major -- intentionally left as major = NULL
-- (unowned / visible to everyone) rather than guessed.

UPDATE activities
SET major = 'วิทยาการคอมพิวเตอร์'
WHERE id IN (5, 6, 7, 8)
  AND major IS NULL;
