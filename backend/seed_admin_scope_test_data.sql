-- ข้อมูลทดสอบระบบแยกแอดมินตามสาขา (โหมด bypass)
-- ไม่แก้ schema เพิ่มแค่ข้อมูล: นักศึกษาทดสอบ + คำขอกิจกรรมภายนอกสถานะ pending
-- ทุกแถวใช้ student_id ขึ้นต้นด้วย TEST- และอีเมล @test.local รันซ้ำได้ (ไม่เพิ่มซ้ำ)
-- ลบออกทั้งหมดด้วย cleanup_admin_scope_test_data.sql
--
-- สาขาต้องสะกดตรงกับ backend/admin_accounts.py
--
-- รัน (Docker):
--   docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backend/seed_admin_scope_test_data.sql

BEGIN;

INSERT INTO students (student_id, first_name, last_name, email, faculty, major)
VALUES
    ('TEST-CHEM-01', 'ทดสอบเคมี', 'หนึ่ง', 'test-chem-01@test.local', 'Faculty of Science', 'เคมี'),
    ('TEST-CHEM-02', 'ทดสอบเคมี', 'สอง', 'test-chem-02@test.local', 'Faculty of Science', 'เคมี'),
    ('TEST-CS-01', 'ทดสอบคอมพิวเตอร์', 'หนึ่ง', 'test-cs-01@test.local', 'Faculty of Science', 'วิทยาการคอมพิวเตอร์'),
    ('TEST-CS-02', 'ทดสอบคอมพิวเตอร์', 'สอง', 'test-cs-02@test.local', 'Faculty of Science', 'วิทยาการคอมพิวเตอร์'),
    -- ไม่มีสาขา: คำขอของคนนี้ต้องเห็นได้เฉพาะแอดมินกลาง
    ('TEST-NOMAJOR-01', 'ทดสอบไม่มีสาขา', 'หนึ่ง', 'test-nomajor-01@test.local', 'Faculty of Science', '')
ON CONFLICT (student_id) DO NOTHING;

CREATE TEMP TABLE seed_external_activities (
    student_id varchar(30),
    title varchar(255),
    skill_key varchar(80),
    level integer
) ON COMMIT DROP;

INSERT INTO seed_external_activities (student_id, title, skill_key, level)
VALUES
    ('TEST-CHEM-01', '[TEST] ค่ายเคมีสัญจร', 'academics', 4),
    ('TEST-CHEM-02', '[TEST] อาสาวิเคราะห์คุณภาพน้ำ', 'volunteerism', 3),
    ('TEST-CS-01', '[TEST] Hackathon เชียงใหม่', 'academics', 5),
    ('TEST-CS-02', '[TEST] สอนเขียนโปรแกรมให้น้องมัธยม', 'volunteerism', 4),
    ('TEST-NOMAJOR-01', '[TEST] จิตอาสาปลูกป่า (ไม่มีสาขา)', 'nature_environmental_conservation', 3);

INSERT INTO external_activities (
    student_id, title, organization, activity_type,
    start_date, end_date, location, role, description, status
)
SELECT
    seed.student_id, seed.title, 'Test Organization', 'จิตอาสา / บริการสังคม',
    DATE '2026-08-15', DATE '2026-08-16', 'Chiang Mai', 'participant',
    'ข้อมูลทดสอบระบบแยกแอดมินตามสาขา', 'pending'
FROM seed_external_activities AS seed
WHERE NOT EXISTS (
    SELECT 1
    FROM external_activities AS existing
    WHERE existing.student_id = seed.student_id
      AND existing.title = seed.title
);

INSERT INTO external_activity_skills (external_activity_id, skill_key, target_role, level)
SELECT activity.id, seed.skill_key, 'participant', seed.level
FROM seed_external_activities AS seed
JOIN external_activities AS activity
  ON activity.student_id = seed.student_id
 AND activity.title = seed.title
ON CONFLICT (external_activity_id, skill_key) DO NOTHING;

COMMIT;
