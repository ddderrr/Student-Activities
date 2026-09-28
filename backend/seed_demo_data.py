"""
เพิ่มข้อมูลตัวอย่าง (demo) ให้หน้า Student Skills มีข้อมูลพอเปรียบเทียบตามสาขา / ชั้นปี

    docker compose exec backend python seed_demo_data.py            # เพิ่ม (ลบ demo เดิมก่อนเสมอ)
    docker compose exec backend python seed_demo_data.py --remove   # ลบเฉพาะข้อมูล demo

ข้อมูล demo แยกจากข้อมูลจริงได้เสมอ และคำสั่ง --remove ลบเฉพาะส่วนนี้:
- รหัสนักศึกษา demo รูปแบบ YY0519NNN (หลักที่ 3-6 เป็น 0519)
- ชื่อกิจกรรม demo ขึ้นต้นด้วย "[Demo] "

นักศึกษาจำลองของหน้าฝั่งนักศึกษา (MOCK_STUDENT_ID ใน frontend/src/constants/currentStudent.js)
จะถูกเพิ่มเข้ากิจกรรม demo ด้วย หน้า My Skills จึงมีข้อมูลให้ดู (--remove ลบแค่การเข้าร่วม ไม่ลบตัวนักศึกษา)
"""

import random
import sys
from datetime import date, datetime

from sqlalchemy.orm import Session

from database import SessionLocal
from main import report_academic_year_be
from models import Activity, ActivityMember, ActivitySkill, Student

DEMO_ID_MARKER = "0519"
DEMO_ACTIVITY_PREFIX = "[Demo] "

MAJORS = [
    "เคมี",
    "ฟิสิกส์และวัสดุศาสตร์",
    "วิทยาการคอมพิวเตอร์",
    "ชีววิทยา",
    "สถิติ",
]

STUDENTS_PER_MAJOR_PER_YEAR = 3

# ต้องตรงกับ MOCK_STUDENT_ID ใน frontend/src/constants/currentStudent.js
MOCK_STUDENT_ID = "670510659"
MOCK_STUDENT_MAJOR = "เคมี"
# (กิจกรรม, บทบาท)
MOCK_STUDENT_ACTIVITIES = [
    ("nature_camp", "participant"),
    ("science_seminar", "participant"),
    ("community_volunteer", "participant"),
    ("exchange_program", "participant"),
    ("lanna_exhibition", "organizer"),
]

FIRST_NAMES = [
    "กฤต", "ขวัญ", "จิรา", "ชนัญ", "ณัฐ", "ดารา", "ธนา", "นภา", "ปวีณ์", "พิม",
    "ภูมิ", "มินตรา", "ยศ", "รวิ", "ลดา", "วรัญ", "ศิริ", "สรวง", "อชิ", "ฮารุ",
]

LAST_NAMES = [
    "แก้วใส", "คำดี", "จันทร์เพ็ญ", "ชัยมงคล", "ทองคำ", "บุญมา", "ปัญญาดี", "พรหมมา",
    "มณีรัตน์", "รุ่งเรือง", "วงศ์ใหญ่", "ศรีสุข", "สายทอง", "อินทร์แก้ว",
]

# (key, ชื่อ, เดือน, participant skills, staff skills)
ACTIVITY_TEMPLATES = [
    ("nature_camp", "ค่ายอนุรักษ์ธรรมชาติดอยสุเทพ", 2,
     {"nature_environmental_conservation": 5, "volunteerism": 4, "health_promotion": 2},
     {"nature_environmental": 5, "creative_leadership": 3}),
    ("wai_khru", "พิธีไหว้ครูคณะวิทยาศาสตร์", 3,
     {"arts_culture_traditions": 5, "academics": 2},
     {"creative_leadership": 4, "promote_equality": 3}),
    ("science_seminar", "สัมมนาวิชาการวิทยาศาสตร์", 5,
     {"academics": 5, "internationalization": 3},
     {"academic": 5, "innovation": 3}),
    ("community_volunteer", "จิตอาสาพัฒนาชุมชน", 7,
     {"volunteerism": 5, "health_promotion": 3, "arts_culture_traditions": 2},
     {"promote_equality": 4, "creative_leadership": 4}),
    ("exchange_program", "Science Exchange Program", 8,
     {"internationalization": 5, "academics": 4, "arts_culture_traditions": 3},
     {"innovation": 3, "academic": 4}),
    ("charity_run", "วิ่งการกุศลเพื่อสุขภาพ", 8,
     {"health_promotion": 5, "volunteerism": 3},
     {"creative_leadership": 3, "entrepreneurship": 2}),
    ("lanna_exhibition", "นิทรรศการศิลปวัฒนธรรมล้านนา", 9,
     {"arts_culture_traditions": 5, "internationalization": 2},
     {"creative_leadership": 4, "innovation": 2}),
    ("hackathon", "Hackathon นวัตกรรมวิทยาศาสตร์", 9,
     {"academics": 4, "internationalization": 2, "health_promotion": 1},
     {"innovation": 5, "entrepreneurship": 4}),
]

# น้ำหนักความสนใจของแต่ละสาขา (ยิ่งมากยิ่งมีโอกาสเข้าร่วม) ให้แต่ละสาขามีรูป skill ต่างกัน
MAJOR_INTERESTS = {
    "เคมี": {"science_seminar": 5, "nature_camp": 4, "hackathon": 3},
    "ฟิสิกส์และวัสดุศาสตร์": {"science_seminar": 5, "exchange_program": 4, "hackathon": 4},
    "วิทยาการคอมพิวเตอร์": {"hackathon": 6, "exchange_program": 4, "science_seminar": 3},
    "ชีววิทยา": {"nature_camp": 6, "community_volunteer": 4, "charity_run": 4},
    "สถิติ": {"science_seminar": 4, "charity_run": 4, "lanna_exhibition": 3},
}

# ปี 1 เน้นกิจกรรมประเพณี / จิตอาสา, ปี 3-4 เน้นวิชาการ / ต่างประเทศ
YEAR_INTERESTS = {
    1: {"wai_khru": 4, "community_volunteer": 4, "lanna_exhibition": 2},
    2: {"community_volunteer": 3, "charity_run": 2, "lanna_exhibition": 2},
    3: {"exchange_program": 3, "science_seminar": 2},
    4: {"exchange_program": 4, "science_seminar": 3, "hackathon": 2},
}


def is_demo_student_id(student_id: str) -> bool:
    return (
        len(student_id) == 9
        and student_id.isascii()
        and student_id.isdigit()
        and student_id[2:6] == DEMO_ID_MARKER
    )


def remove_demo_data(db: Session) -> tuple[int, int]:
    activities = (
        db.query(Activity)
        .filter(Activity.name.startswith(DEMO_ACTIVITY_PREFIX))
        .all()
    )
    students = [
        student
        for student in db.query(Student).all()
        if is_demo_student_id(student.student_id)
    ]

    # ORM cascade ลบ activity_members / activity_skills ที่ผูกอยู่ให้ด้วย
    for activity in activities:
        db.delete(activity)
    for student in students:
        db.delete(student)

    db.commit()
    return len(students), len(activities)


def seed_demo_data(db: Session, today: date | None = None) -> dict:
    today = today or date.today()
    rng = random.Random(42)  # ผลเหมือนเดิมทุกครั้งที่รัน

    remove_demo_data(db)

    year = today.year
    academic_year = report_academic_year_be(year, "ALL", today)

    activities = {}
    for key, name, month, participant_skills, staff_skills in ACTIVITY_TEMPLATES:
        start_at = datetime(year, month, 10, 9, 0, 0)
        activity = Activity(
            activity_type="Demo",
            name=f"{DEMO_ACTIVITY_PREFIX}{name}",
            start_at=start_at,
            end_at=datetime(year, month, 10, 16, 0, 0),
            department="คณะวิทยาศาสตร์",
            responsible_person="Demo Staff",
            advisor="",
            location="มหาวิทยาลัยเชียงใหม่",
            description="ข้อมูลตัวอย่างสำหรับทดสอบหน้า Student Skills",
            skill_levels=[
                ActivitySkill(skill_key=skill_key, target_role="participant", level=level)
                for skill_key, level in participant_skills.items()
            ] + [
                ActivitySkill(skill_key=skill_key, target_role="staff", level=level)
                for skill_key, level in staff_skills.items()
            ],
        )
        db.add(activity)
        activities[key] = activity

    db.flush()

    student_count = 0
    membership_count = 0

    for major_index, major in enumerate(MAJORS):
        for level in range(1, 5):
            entry_year_be = academic_year - (level - 1)

            for number in range(STUDENTS_PER_MAJOR_PER_YEAR):
                running = major_index * 100 + level * 10 + number + 1
                student_id = f"{entry_year_be - 2500:02d}{DEMO_ID_MARKER}{running:03d}"

                db.add(
                    Student(
                        student_id=student_id,
                        first_name=rng.choice(FIRST_NAMES),
                        last_name=rng.choice(LAST_NAMES),
                        email=f"demo.{student_id}@cmu.ac.th",
                        faculty="Faculty of Science",
                        major=major,
                    )
                )
                student_count += 1

                # ปี 1 เพิ่งเข้าเรียนเดือนกรกฎาคม จึงเข้าได้แค่กิจกรรมตั้งแต่ ก.ค.
                eligible = [
                    key for key, _name, month, _p, _s in ACTIVITY_TEMPLATES
                    if level > 1 or month >= 7
                ]
                weights = {
                    key: 1
                    + MAJOR_INTERESTS[major].get(key, 0)
                    + YEAR_INTERESTS[level].get(key, 0)
                    for key in eligible
                }

                join_count = min(len(eligible), rng.randint(2, 4))
                joined = []
                while len(joined) < join_count:
                    pool = [key for key in eligible if key not in joined]
                    joined.append(rng.choices(pool, [weights[key] for key in pool])[0])

                for key in joined:
                    # รุ่นพี่มีโอกาสเป็นผู้จัดมากกว่า
                    role = "organizer" if rng.random() < 0.05 * level else "participant"
                    db.add(
                        ActivityMember(
                            activity_id=activities[key].id,
                            student_id=student_id,
                            role=role,
                        )
                    )
                    membership_count += 1

    # นักศึกษาจำลองของหน้าฝั่งนักศึกษา: สร้างแบบเดียวกับ backend ถ้ายังไม่มี และเติมสาขาถ้ายังว่าง
    mock_student = db.get(Student, MOCK_STUDENT_ID)
    if not mock_student:
        mock_student = Student(
            student_id=MOCK_STUDENT_ID,
            first_name="Demo",
            last_name="Student",
            email="",
            faculty="Faculty of Science",
            major=MOCK_STUDENT_MAJOR,
        )
        db.add(mock_student)
    elif not mock_student.major:
        mock_student.major = MOCK_STUDENT_MAJOR

    db.flush()

    for key, role in MOCK_STUDENT_ACTIVITIES:
        db.add(
            ActivityMember(
                activity_id=activities[key].id,
                student_id=MOCK_STUDENT_ID,
                role=role,
            )
        )

    db.commit()

    return {
        "students": student_count,
        "activities": len(activities),
        "memberships": membership_count,
        "mock_student_activities": len(MOCK_STUDENT_ACTIVITIES),
        "year": year,
    }


def main() -> None:
    with SessionLocal() as db:
        if "--remove" in sys.argv:
            students, activities = remove_demo_data(db)
            print(f"ลบข้อมูล demo แล้ว: นักศึกษา {students} คน, กิจกรรม {activities} กิจกรรม")
            return

        result = seed_demo_data(db)
        print(
            f"เพิ่มข้อมูล demo แล้ว: นักศึกษา {result['students']} คน, "
            f"กิจกรรม {result['activities']} กิจกรรม, "
            f"การเข้าร่วม {result['memberships']} รายการ (ปี {result['year']}) "
            f"+ นักศึกษาจำลอง {MOCK_STUDENT_ID} เข้าร่วม {result['mock_student_activities']} กิจกรรม"
        )


if __name__ == "__main__":
    main()
