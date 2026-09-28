-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
-- create_all() does not add columns to tables that already exist.
--
-- เพิ่ม activities.major สำหรับ major-scoping ของกิจกรรม (เหมือน students.major)
-- NULL = สร้างโดยแอดมินกลาง หรือกิจกรรมเก่าก่อนมีคอลัมน์นี้ -> เห็นได้ทุกแอดมิน
-- แถวเดิมทั้งหมดจะได้ค่า NULL อัตโนมัติจาก ALTER TABLE นี้ (ตามที่ตั้งใจไว้)

ALTER TABLE activities
ADD COLUMN IF NOT EXISTS major VARCHAR(255);
