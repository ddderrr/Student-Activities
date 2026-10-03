-- Run this ONCE on the existing PostgreSQL database (safe to re-run: guarded by app_migrations).
--
-- B28: ก่อนหน้านี้คอลัมน์ที่ใช้ server_default now() บันทึกเวลา UTC (session ของ container
-- ฐานข้อมูลเป็น UTC) แต่เวลาจาก Python (decided_at, submitted_at ตอนส่งใหม่) เป็นเวลาไทย
-- ตอนนี้ทุกที่ใช้เวลาไทย (backend/timeutil.py) ไฟล์นี้เลื่อนข้อมูลเดิมที่เป็น UTC ไป +7 ชั่วโมง
--
-- ไม่แตะ: decided_at (ตั้งจาก Python เป็นเวลาไทยอยู่แล้ว), admin_notifications /
-- admin_notification_reads (TIMESTAMPTZ เก็บเวลาที่แน่นอนอยู่แล้ว)

CREATE TABLE IF NOT EXISTS app_migrations (
    name VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM app_migrations WHERE name = 'bangkok_timestamps') THEN
        RAISE NOTICE 'bangkok_timestamps already applied, skipping';
        RETURN;
    END IF;

    -- external_activities.submitted_at: ตอนส่งครั้งแรกมาจาก DB now() (UTC) ตรงกับเวลาที่อัปโหลด
    -- หลักฐาน (UTC เหมือนกัน) ส่วนที่ส่งใหม่หลังถูกปฏิเสธตั้งจาก Python (เวลาไทยอยู่แล้ว) จึงเลื่อน
    -- เฉพาะแถวที่ submitted_at ใกล้กับเวลาอัปโหลดหลักฐานไฟล์แรก (ภายใน 1 นาที)
    UPDATE external_activities e
    SET submitted_at = e.submitted_at + interval '7 hours'
    WHERE EXISTS (
        SELECT 1 FROM external_activity_evidence ev
        WHERE ev.external_activity_id = e.id
        GROUP BY ev.external_activity_id
        HAVING abs(extract(epoch FROM e.submitted_at - min(ev.created_at))) < 60
    );

    -- คอลัมน์ที่ตั้งจาก DB now() อย่างเดียวมาตลอด
    UPDATE external_activity_evidence SET created_at = created_at + interval '7 hours';
    UPDATE students SET created_at = created_at + interval '7 hours';
    UPDATE activities SET created_at = created_at + interval '7 hours';
    UPDATE activity_members SET created_at = created_at + interval '7 hours';
    UPDATE admins SET created_at = created_at + interval '7 hours';
    UPDATE notifications SET created_at = created_at + interval '7 hours';
    UPDATE student_requests SET submitted_at = submitted_at + interval '7 hours';
    UPDATE student_skill_benchmarks SET updated_at = updated_at + interval '7 hours';

    INSERT INTO app_migrations (name) VALUES ('bangkok_timestamps');
END $$;

-- เครื่องมืออื่นที่ต่อฐานข้อมูลนี้ (psql, DBeaver) เห็นเวลาเป็นเวลาไทยด้วย
ALTER DATABASE student_activities SET timezone TO 'Asia/Bangkok';
