-- ลบข้อมูลเดโมจาก seed_transcript_demo_data.sql
-- กิจกรรมของคณะ (uid DEMO-TR-*) และนักศึกษา 670510999
-- member/skill/external activities ถูกลบตาม (ON DELETE CASCADE) ส่วน notifications ลบเอง

BEGIN;

DELETE FROM activities
WHERE uid LIKE 'DEMO-TR-%';

DELETE FROM notifications
WHERE student_id = '670510999';

DELETE FROM students
WHERE student_id = '670510999'
  AND email = 'demo-transcript@test.local';

COMMIT;
