-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
-- create_all() does not add columns or change constraints on tables that already exist.
--
-- หลักฐานเปลี่ยนจาก 1 ไฟล์ต่อคำขอ (คอลัมน์ evidence_* ใน external_activities)
-- เป็นหลายไฟล์ต่อคำขอ (ตาราง external_activity_evidence สูงสุด 10 ไฟล์)
--
-- ลำดับ:
--   1. รันไฟล์นี้
--   2. รัน migrate_evidence_files.py เพื่อย้ายไฟล์เข้าโฟลเดอร์ uploads/external_activities/<id>/
--      (ระหว่างยังไม่ได้ย้าย backend ยังอ่านไฟล์จากที่เดิมได้)

BEGIN;

-- 1) ตารางใหม่ (โครงสร้างเดียวกับ models.ExternalActivityEvidence)
CREATE TABLE IF NOT EXISTS external_activity_evidence (
    id SERIAL PRIMARY KEY,
    external_activity_id INTEGER NOT NULL
        REFERENCES external_activities (id) ON DELETE CASCADE,
    stored_name VARCHAR(100) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_external_activity_evidence_id
    ON external_activity_evidence (id);

CREATE INDEX IF NOT EXISTS ix_external_activity_evidence_external_activity_id
    ON external_activity_evidence (external_activity_id);

-- 2) คัดลอกไฟล์หลักฐานของคำขอเดิมเข้าตารางใหม่ (ข้ามแถวที่คัดลอกไปแล้ว)
INSERT INTO external_activity_evidence (
    external_activity_id,
    stored_name,
    original_name,
    content_type,
    size,
    created_at
)
SELECT
    ea.id,
    ea.evidence_filename,
    ea.evidence_original_name,
    ea.evidence_content_type,
    ea.evidence_size,
    ea.submitted_at
FROM external_activities ea
WHERE ea.evidence_filename IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM external_activity_evidence e
      WHERE e.external_activity_id = ea.id
        AND e.stored_name = ea.evidence_filename
  );

-- 3) คอลัมน์เดิมเลิกใช้ แต่ยังเก็บข้อมูลไว้เผื่อย้อนกลับ: ให้เป็น NULL ได้
--    เพราะคำขอใหม่จะไม่เขียนคอลัมน์เหล่านี้แล้ว
ALTER TABLE external_activities
    ALTER COLUMN evidence_filename DROP NOT NULL,
    ALTER COLUMN evidence_original_name DROP NOT NULL,
    ALTER COLUMN evidence_content_type DROP NOT NULL,
    ALTER COLUMN evidence_size DROP NOT NULL;

COMMIT;
