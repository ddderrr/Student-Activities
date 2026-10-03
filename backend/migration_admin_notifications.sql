-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
-- (backend สร้างตารางให้เองตอนเริ่มทำงานผ่าน create_all ไฟล์นี้ไว้สำหรับรันเองหรือดูโครงสร้าง)
--
-- กระดิ่งแจ้งเตือนฝั่งแอดมิน: นักศึกษาส่ง / ส่งใหม่คำขอกิจกรรมภายนอก
-- major = สาขาของนักศึกษา (แอดมินสาขาเห็นเฉพาะสาขาตัวเอง แอดมินกลางเห็นทั้งหมด)
-- สถานะอ่านแล้วแยกต่อแอดมิน (admin_notification_reads)

CREATE TABLE IF NOT EXISTS admin_notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(40) NOT NULL
        CONSTRAINT ck_admin_notification_type CHECK (type IN ('external_submitted', 'external_resubmitted')),
    major VARCHAR(255),
    student_id VARCHAR(30) NOT NULL,
    student_name VARCHAR(300) NOT NULL DEFAULT '',
    activity_title VARCHAR(255) NOT NULL DEFAULT '',
    external_activity_id INTEGER REFERENCES external_activities(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    link VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_admin_notifications_major ON admin_notifications (major);
CREATE INDEX IF NOT EXISTS ix_admin_notifications_external_activity_id ON admin_notifications (external_activity_id);
CREATE INDEX IF NOT EXISTS ix_admin_notifications_created_at ON admin_notifications (created_at);

CREATE TABLE IF NOT EXISTS admin_notification_reads (
    notification_id INTEGER NOT NULL REFERENCES admin_notifications(id) ON DELETE CASCADE,
    admin_email VARCHAR(255) NOT NULL,
    read_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (notification_id, admin_email)
);
