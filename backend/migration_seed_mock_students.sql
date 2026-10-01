-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
--
-- เพิ่มนักศึกษาจำลอง 2 คนสำหรับทดสอบหน้า login ฝั่งนักศึกษา (bypass mode ผ่าน
-- X-Student-Email เหมือนแอดมิน) คนละสาขา ใช้ทดสอบ major-scoping ของกิจกรรม /
-- การอนุมัติกิจกรรมภายนอกจากมุมมองนักศึกษาจริง
--
-- อีเมล + student_id ต้องตรงกับ backend/student_bypass.py::STUDENT_LOGIN_ACCOUNTS

INSERT INTO students (student_id, first_name, last_name, email, faculty, major)
VALUES
    ('670510001', 'นักศึกษา', 'เคมี', 'chem@test.com', 'คณะวิทยาศาสตร์', 'เคมี'),
    ('670510002', 'นักศึกษา', 'คอมพิวเตอร์', 'cs@test.com', 'คณะวิทยาศาสตร์', 'วิทยาการคอมพิวเตอร์')
ON CONFLICT (student_id) DO NOTHING;
