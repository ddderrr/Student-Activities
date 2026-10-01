-- ข้อมูลเดโม Transcript PDF: นักศึกษาชั้นปีที่ 3 (รหัส 67xxxxxxx) พร้อมกิจกรรม 3 ปีการศึกษา
-- ต้องรัน migration_add_activity_major.sql ก่อน
-- กิจกรรมของคณะใช้ uid ขึ้นต้นด้วย DEMO-TR- / นักศึกษาใช้อีเมล demo@test.com รันซ้ำได้ (ไม่เพิ่มซ้ำ)
-- ลบออกทั้งหมดด้วย cleanup_transcript_demo_data.sql
-- เปิดดู: หน้า login นักศึกษา ใช้ demo@test.com รหัสผ่าน 1234 (ได้นักศึกษา 670510999) แล้วไปเมนู Transcript
--
-- ปีการศึกษาเริ่มเดือนกรกฎาคม (academic_calendar.ACADEMIC_YEAR_START_MONTH)
--   2567 = ก.ค. 2024 - มิ.ย. 2025 (ชั้นปีที่ 1)
--   2568 = ก.ค. 2025 - มิ.ย. 2026 (ชั้นปีที่ 2)
--   2569 = ก.ค. 2026 - มิ.ย. 2027 (ชั้นปีที่ 3)

BEGIN;

INSERT INTO students (student_id, first_name, last_name, email, faculty, major)
VALUES ('670510999', 'สมหญิง', 'ใจดีมีน้ำใจ', 'demo@test.com', 'Faculty of Science', 'เคมี')
ON CONFLICT (student_id) DO NOTHING;

CREATE TEMP TABLE seed_activities (
    uid varchar(30),
    name varchar(255),
    activity_type varchar(120),
    start_at timestamp,
    major varchar(255),
    role varchar(20),
    skills jsonb
) ON COMMIT DROP;

INSERT INTO seed_activities VALUES
    ('DEMO-TR-01', 'ปฐมนิเทศนักศึกษาใหม่ คณะวิทยาศาสตร์', 'กิจกรรมวิชาการ', '2024-07-10 09:00', NULL, 'participant',
     '{"academics": 4, "arts_culture_traditions": 3}'),
    ('DEMO-TR-02', 'พิธีไหว้ครูคณะวิทยาศาสตร์', 'ศิลปวัฒนธรรม', '2024-08-15 09:00', NULL, 'participant',
     '{"arts_culture_traditions": 5}'),
    ('DEMO-TR-03', 'ค่ายพัฒนาทักษะห้องปฏิบัติการเคมี', 'กิจกรรมวิชาการ', '2025-01-20 09:00', 'เคมี', 'participant',
     '{"academics": 4, "health_promotion": 3}'),
    ('DEMO-TR-04', 'ค่ายเคมีสัญจรสู่โรงเรียนมัธยม', 'จิตอาสา', '2025-07-12 09:00', 'เคมี', 'participant',
     '{"academics": 3, "volunteerism": 5}'),
    ('DEMO-TR-05', 'งานวันวิทยาศาสตร์แห่งชาติ', 'นิทรรศการ', '2025-08-18 09:00', NULL, 'organizer',
     '{"innovation": 4}'),
    ('DEMO-TR-06', 'สัมมนาวิชาการเคมีสีเขียวเพื่อสิ่งแวดล้อม', 'สัมมนา', '2026-07-05 09:00', 'เคมี', 'participant',
     '{"academics": 5, "nature_environmental_conservation": 4}'),
    ('DEMO-TR-07', 'Data Science Hackathon', 'การแข่งขัน', '2026-08-10 09:00', 'วิทยาการคอมพิวเตอร์', 'participant',
     '{"academics": 4, "internationalization": 3}');

INSERT INTO activities (
    uid, activity_type, name, start_at, end_at, department, major,
    responsible_person, advisor, location, description, status
)
SELECT
    seed.uid, seed.activity_type, seed.name, seed.start_at, seed.start_at + interval '7 hours',
    '', seed.major, 'ฝ่ายกิจการนักศึกษา', '', 'คณะวิทยาศาสตร์ มช.',
    'ข้อมูลเดโม Transcript PDF', 'completed'
FROM seed_activities AS seed
ON CONFLICT (uid) DO NOTHING;

INSERT INTO activity_members (activity_id, student_id, role)
SELECT activity.id, '670510999', seed.role
FROM seed_activities AS seed
JOIN activities AS activity ON activity.uid = seed.uid
ON CONFLICT (activity_id, student_id) DO NOTHING;

INSERT INTO activity_skills (activity_id, skill_key, target_role, level)
SELECT
    activity.id,
    skill.key,
    CASE WHEN seed.role = 'participant' THEN 'participant' ELSE 'staff' END,
    skill.value::int
FROM seed_activities AS seed
JOIN activities AS activity ON activity.uid = seed.uid
CROSS JOIN LATERAL jsonb_each_text(seed.skills) AS skill
ON CONFLICT (activity_id, skill_key, target_role) DO NOTHING;

CREATE TEMP TABLE seed_external (
    title varchar(255),
    organization varchar(255),
    start_date date,
    status varchar(20),
    skills jsonb
) ON COMMIT DROP;

INSERT INTO seed_external VALUES
    ('อาสาปลูกป่าต้นน้ำ ดอยสุเทพ', 'มูลนิธิรักษ์ป่าเชียงใหม่', '2026-02-01', 'approved',
     '{"volunteerism": 4, "nature_environmental_conservation": 5}'),
    ('International Chemistry Olympiad Workshop', 'Chemical Society of Thailand', '2026-07-20', 'approved',
     '{"internationalization": 4, "academics": 5}'),
    -- ยังไม่อนุมัติ: ต้องไม่อยู่ใน transcript
    ('อบรมความปลอดภัยในห้องปฏิบัติการ (รออนุมัติ)', 'สมาคมความปลอดภัย', '2026-09-01', 'pending',
     '{"health_promotion": 4}');

INSERT INTO external_activities (
    student_id, title, organization, activity_type,
    start_date, end_date, location, role, description, status, decided_at
)
SELECT
    '670510999', seed.title, seed.organization, 'อบรม / Workshop',
    seed.start_date, seed.start_date, 'เชียงใหม่', 'participant',
    'ข้อมูลเดโม Transcript PDF', seed.status,
    CASE WHEN seed.status = 'approved' THEN seed.start_date + 7 END
FROM seed_external AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM external_activities AS existing
    WHERE existing.student_id = '670510999' AND existing.title = seed.title
);

INSERT INTO external_activity_skills (external_activity_id, skill_key, target_role, level)
SELECT activity.id, skill.key, 'participant', skill.value::int
FROM seed_external AS seed
JOIN external_activities AS activity
  ON activity.student_id = '670510999' AND activity.title = seed.title
CROSS JOIN LATERAL jsonb_each_text(seed.skills) AS skill
ON CONFLICT (external_activity_id, skill_key) DO NOTHING;

COMMIT;
