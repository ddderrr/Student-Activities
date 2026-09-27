-- Run this ONCE on the existing PostgreSQL database.
-- create_all() does not add columns to tables that already exist.
-- (ตาราง notifications ไม่ต้องสร้างเอง create_all() จะสร้างให้ตอน backend start)

ALTER TABLE student_requests
ADD COLUMN IF NOT EXISTS reject_reason TEXT;
