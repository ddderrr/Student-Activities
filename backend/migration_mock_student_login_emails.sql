-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
--
-- หน้า login นักศึกษาเปลี่ยนเป็นอีเมล + รหัสผ่าน: นักศึกษาจำลองสาขาเดียวกันใช้อีเมล
-- ร่วมกัน (รหัสผ่าน 1234 ดู backend/student_bypass.py) login แล้วได้คนหลักของสาขา
-- (670510001 / 670510002) ตาม STUDENT_LOGIN_ACCOUNTS
--
-- รวมนักศึกษาจาก migration_seed_mock_students.sql (2 คน) และ
-- migration_seed_branch_roster_students.sql (10 คน)

UPDATE students
SET email = 'chem@test.com'
WHERE student_id IN ('670510001', '670510201', '670510202', '670510203', '670510204', '670510205');

UPDATE students
SET email = 'cs@test.com'
WHERE student_id IN ('670510002', '670510101', '670510102', '670510103', '670510104', '670510105');
