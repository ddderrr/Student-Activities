-- ลบข้อมูลทดสอบจาก seed_admin_scope_test_data.sql
-- external_activities / skills / evidence / activity_members ถูกลบตาม (ON DELETE CASCADE)
-- ส่วน notifications ไม่มี FK ไปที่ students จึงลบเองก่อน
--
-- รัน (Docker):
--   docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backend/cleanup_admin_scope_test_data.sql

BEGIN;

DELETE FROM notifications
WHERE student_id LIKE 'TEST-%';

DELETE FROM students
WHERE student_id LIKE 'TEST-%'
  AND email LIKE '%@test.local';

COMMIT;
