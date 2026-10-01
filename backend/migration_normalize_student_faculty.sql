-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
--
-- ชื่อคณะของนักศึกษาใช้ค่าเดียวกันทั้งระบบ: 'Faculty of Science' (ค่าเริ่มต้นตอน
-- import นักศึกษา และ default ของ students.faculty ใน models.py)
-- นักศึกษาจำลองจาก migration_seed_mock_students.sql และ
-- migration_seed_branch_roster_students.sql เคยใช้ 'คณะวิทยาศาสตร์'

UPDATE students
SET faculty = 'Faculty of Science'
WHERE faculty = 'คณะวิทยาศาสตร์';
