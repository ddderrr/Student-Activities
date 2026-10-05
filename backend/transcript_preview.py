"""ข้อมูลนักศึกษาตัวอย่างสำหรับดูหน้าตา Transcript ในหน้า Settings (ไม่ได้อ่านจากฐานข้อมูล)"""

from datetime import date

import transcript_data
from models import Student

SAMPLE_STUDENT = {
    "student_id": "670510123",
    "first_name": "นักศึกษา",
    "last_name": "ตัวอย่าง",
    "major": "วิทยาการคอมพิวเตอร์",
}

# (ชื่อ, ประเภท, ผู้จัด, สาขาผู้จัด, วันที่, บทบาท, source, ชั่วโมง, ทักษะ)
SAMPLE_ACTIVITIES = [
    ("ปฐมนิเทศนักศึกษาใหม่", "Academic", "คณะวิทยาศาสตร์", None, date(2024, 7, 15), "participant", "faculty", 3,
     {"academics": 4, "arts_culture_traditions": 3}),
    ("ค่ายอาสาพัฒนาชนบท", "Volunteer", "คณะวิทยาศาสตร์", None, date(2024, 11, 9), "organizer", "faculty", 24, {}),
    ("Coding Bootcamp", "Academic", "", "วิทยาการคอมพิวเตอร์", date(2025, 2, 22), "participant", "major", 12,
     {"academics": 5, "internationalization": 3}),
    ("ปลูกป่าชายเลน", "จิตอาสา / บริการสังคม", "มูลนิธิรักษ์ธรรมชาติ", None, date(2025, 8, 30), "participant", "external", 6,
     {"nature_environmental_conservation": 5, "volunteerism": 4}),
    ("วิ่งเพื่อสุขภาพ Science Run", "Sport", "คณะวิทยาศาสตร์", None, date(2025, 12, 7), "participant", "faculty", 2,
     {"health_promotion": 4}),
]


def sample_transcript() -> dict:
    student = Student(**SAMPLE_STUDENT, faculty="Faculty of Science")
    items = [
        {
            "key": f"sample-{index}",
            "title": title,
            "activity_type": activity_type,
            "organizer": organizer or f"สาขา{major}",
            "organizer_major": major,
            "organizer_department": organizer or None,
            "date": day,
            "role": role,
            "source": source,
            # กิจกรรมตัวอย่างจบแล้วทั้งหมด ชั่วโมงที่ได้ = ชั่วโมงของกิจกรรม
            "activity_hours": float(hours),
            "earned_activity_hours": float(hours),
            "skills": skills,
        }
        for index, (title, activity_type, organizer, major, day, role, source, hours, skills) in enumerate(SAMPLE_ACTIVITIES)
    ]
    return transcript_data.build_transcript(student, items)
