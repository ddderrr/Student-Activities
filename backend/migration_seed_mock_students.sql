-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
--
-- เพิ่มนักศึกษาจำลอง 2 คนสำหรับทดสอบหน้า login ฝั่งนักศึกษา (bypass mode ผ่าน
-- X-Student-Email เหมือนแอดมิน) คนละสาขา ใช้ทดสอบ major-scoping ของกิจกรรม /
-- การอนุมัติกิจกรรมภายนอกจากมุมมองนักศึกษาจริง
--
-- อีเมลต้องตรงกับ backend/student_bypass.py::STUDENT_BYPASS_EMAILS

INSERT INTO students (student_id, first_name, last_name, email, faculty, major)
VALUES
    ('670510001', 'นักศึกษา', 'เคมี', 'chem_student@test.local', 'คณะวิทยาศาสตร์', 'เคมี'),
    ('670510002', 'นักศึกษา', 'คอมพิวเตอร์', 'cs_student@test.local', 'คณะวิทยาศาสตร์', 'วิทยาการคอมพิวเตอร์')
ON CONFLICT (student_id) DO NOTHING;
