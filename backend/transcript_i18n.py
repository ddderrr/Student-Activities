"""ข้อความของ Transcript PDF สองภาษา (lang = "th" | "en")

ข้อความคงที่ (หัวข้อ, ป้าย, บทบาท, ประเภท, ทักษะ, สาขา) แปลที่นี่ที่เดียว
ข้อมูลที่ผู้ใช้กรอกเอง (ชื่อนักศึกษา, ชื่อกิจกรรม, ผู้จัด) แสดงตามที่บันทึกไว้ แปลอัตโนมัติไม่ได้

ภาษาไทย: วันที่และปีการศึกษาเป็น พ.ศ. / ภาษาอังกฤษ: ค.ศ.
"""

from datetime import date

import transcript_config
from skill_definitions import PARTICIPANT_SKILL_DEFINITIONS

LANGUAGES = ("th", "en")

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]
THAI_MONTHS_SHORT = [
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]
ENGLISH_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# ต้องตรงกับ branches.py / frontend/src/constants/branches.js
MAJOR_NAMES_EN = {
    "เคมี": "Chemistry",
    "เคมีอุตสาหกรรม": "Industrial Chemistry",
    "จุลชีววิทยา": "Microbiology",
    "ชีวเคมีและชีวเคมีนวัตกรรม": "Biochemistry and Biochemical Innovation",
    "ชีววิทยา": "Biology",
    "ธรณีวิทยา": "Geology",
    "ฟิสิกส์": "Physics",
    "วัสดุศาสตร์": "Materials Science",
    "สัตววิทยา": "Zoology",
    "คณิตศาสตร์": "Mathematics",
    "วิทยาการข้อมูล": "Data Science",
    "วิทยาการคอมพิวเตอร์": "Computer Science",
    "วิทยาศาสตร์สิ่งแวดล้อม (หลักสูตรนานาชาติ)": "Environmental Science (International Program)",
    "สถิติ": "Statistics",
    "อัญมณีวิทยา": "Gemology",
    # ชื่อเดิมในข้อมูลเก่า
    "ฟิสิกส์และวัสดุศาสตร์": "Physics and Materials Science",
}

# ประเภทกิจกรรมภายนอก (frontend/src/constants/currentStudent.js EXTERNAL_ACTIVITY_CATEGORIES)
ACTIVITY_TYPES_EN = {
    "จิตอาสา / บริการสังคม": "Volunteer / Community Service",
    "อบรม / Workshop": "Training / Workshop",
    "สัมมนา / ประชุมวิชาการ": "Seminar / Academic Conference",
    "การแข่งขัน": "Competition",
    "ค่ายกิจกรรม": "Camp",
    "ศิลปะและวัฒนธรรม": "Arts and Culture",
    "กีฬาและสุขภาพ": "Sports and Health",
    "อื่น ๆ": "Other",
}

SKILL_LABELS = {
    "th": {
        "arts_culture_traditions": "ศิลปะ วัฒนธรรม และประเพณี",
        "volunteerism": "จิตอาสาและการมีส่วนร่วมเพื่อสังคม",
        "academics": "การเรียนรู้และพัฒนาทางวิชาการ",
        "internationalization": "ความเป็นสากลและการเรียนรู้ข้ามวัฒนธรรม",
        "health_promotion": "การส่งเสริมสุขภาพและความเป็นอยู่ที่ดี",
        "nature_environmental_conservation": "การอนุรักษ์ธรรมชาติและสิ่งแวดล้อม",
    },
    "en": dict(PARTICIPANT_SKILL_DEFINITIONS),
}

TEXT = {
    "th": {
        "university": transcript_config.UNIVERSITY_NAME,
        "faculty": transcript_config.FACULTY_NAME,
        "faculty_and_university": f"{transcript_config.FACULTY_NAME} {transcript_config.UNIVERSITY_NAME}",
        "title": transcript_config.DOCUMENT_TITLE,
        "logo_placeholder": transcript_config.LOGO_PLACEHOLDER_TEXT,
        "signer_name": transcript_config.SIGNER_NAME,
        "signer_position": transcript_config.SIGNER_POSITION,
        "verify": transcript_config.VERIFY_TEXT,
        "watermark": transcript_config.WATERMARK_TEXT,
        "document_number_short": "เลขที่",
        "page": "หน้า",
        "name": "ชื่อ-สกุล",
        "student_id": "รหัสนักศึกษา",
        "major": "สาขาวิชา",
        "year_level": "ชั้นปี",
        "document_number": "เลขที่เอกสาร",
        "issued_on": "วันที่ออกเอกสาร",
        "scope": "ประเภทกิจกรรม",
        "year_range": "ช่วงชั้นปี",
        "activities_heading": "รายการกิจกรรม",
        "no": "ที่",
        "date": "วันที่",
        "activity_and_organizer": "ชื่อกิจกรรม / ผู้จัด",
        "source": "ประเภท",
        "role": "บทบาท",
        "empty": "ไม่มีกิจกรรมตามเงื่อนไขที่เลือก",
        "summary_heading": "สรุปจำนวนกิจกรรม",
        "total": "รวมทั้งหมด",
        "skills_heading": "คะแนนทักษะ",
        "skills_heading_out_of_5": "คะแนนทักษะ (เต็ม 5)",
        "skills_note": 'คะแนนคิดจากค่าเฉลี่ยของกิจกรรมในเอกสารนี้ที่เข้าร่วมในบทบาทผู้เข้าร่วม ("-" = ยังไม่มีกิจกรรมที่ให้ทักษะนี้)',
        "skills_note_out_of_5": 'เต็ม 5 คิดจากค่าเฉลี่ยของกิจกรรมในเอกสารนี้ที่เข้าร่วมในบทบาทผู้เข้าร่วม ("-" = ยังไม่มีกิจกรรมที่ให้ทักษะนี้)',
        "sign_here": "ลงชื่อ ..............................................",
        "date_prefix": "วันที่",
        "qr_placeholder": "[QR ตรวจสอบเอกสาร]",
        "academic_year": "ปีการศึกษา {year}",
        "year_level_n": "ชั้นปีที่ {level}",
        "all_years": "ทุกชั้นปี",
        "year_levels": "ชั้นปีที่ {levels}",
        "scopes": {
            "all": "กิจกรรมทั้งหมด",
            "major": "เฉพาะกิจกรรมของสาขา",
            "faculty": "เฉพาะกิจกรรมส่วนกลางของคณะ",
            "external": "เฉพาะกิจกรรมภายนอก",
        },
        "sources": {"faculty": "กิจกรรมคณะ", "major": "กิจกรรมสาขา", "other_major": "กิจกรรมสาขา", "external": "กิจกรรมภายนอก"},
        "roles": {"participant": "ผู้เข้าร่วม", "organizer": "ผู้จัด / ทีมงาน"},
        "major_organizer": "สาขา{major}",
    },
    "en": {
        "university": transcript_config.UNIVERSITY_NAME_EN,
        "faculty": transcript_config.FACULTY_SHORT_NAME_EN,
        "faculty_and_university": transcript_config.FACULTY_NAME_EN,
        "title": transcript_config.DOCUMENT_TITLE_EN,
        "logo_placeholder": transcript_config.LOGO_PLACEHOLDER_TEXT_EN,
        "signer_name": transcript_config.SIGNER_NAME_EN,
        "signer_position": transcript_config.SIGNER_POSITION_EN,
        "verify": transcript_config.VERIFY_TEXT_EN,
        "watermark": transcript_config.WATERMARK_TEXT_EN,
        "document_number_short": "No.",
        "page": "Page",
        "name": "Name",
        "student_id": "Student ID",
        "major": "Major",
        "year_level": "Year",
        "document_number": "Document No.",
        "issued_on": "Date of Issue",
        "scope": "Activities",
        "year_range": "Years",
        "activities_heading": "Activities",
        "no": "No.",
        "date": "Date",
        "activity_and_organizer": "Activity / Organizer",
        "source": "Type",
        "role": "Role",
        "empty": "No activities match the selected options",
        "summary_heading": "Activity Summary",
        "total": "Total",
        "skills_heading": "Skill Scores",
        "skills_heading_out_of_5": "Skill Scores (out of 5)",
        "skills_note": 'Scores are the average of the activities in this document joined as a participant ("-" = no activity for this skill yet).',
        "skills_note_out_of_5": 'Out of 5, averaged over the activities in this document joined as a participant ("-" = no activity for this skill yet).',
        "sign_here": "Signature ..............................................",
        "date_prefix": "Date",
        "qr_placeholder": "[Verification QR]",
        "academic_year": "Academic Year {year}",
        "year_level_n": "Year {level}",
        "all_years": "All years",
        "year_levels": "Year {levels}",
        "scopes": {
            "all": "All activities",
            "major": "Major activities only",
            "faculty": "Faculty-wide activities only",
            "external": "External activities only",
        },
        "sources": {"faculty": "Faculty", "major": "Major", "other_major": "Major", "external": "External"},
        "roles": {"participant": "Participant", "organizer": "Organizer / Staff"},
        "major_organizer": "Department of {major}",
    },
}


def major_name(major: str | None, lang: str) -> str:
    major = (major or "").strip()
    if lang == "en":
        return MAJOR_NAMES_EN.get(major, major)
    return major


def activity_type_name(activity_type: str | None, lang: str) -> str:
    value = (activity_type or "").strip()
    if lang == "en":
        return ACTIVITY_TYPES_EN.get(value, value)
    return value


def format_date(value: date, lang: str) -> str:
    if lang == "en":
        return f"{value.day} {ENGLISH_MONTHS[value.month - 1]} {value.year}"
    return f"{value.day} {THAI_MONTHS[value.month - 1]} {value.year + 543}"


def format_date_short(value: date, lang: str) -> str:
    if lang == "en":
        return f"{value.day} {ENGLISH_MONTHS[value.month - 1][:3]} {value.year}"
    return f"{value.day} {THAI_MONTHS_SHORT[value.month - 1]} {value.year + 543}"


def academic_year_label(buddhist_year: int, lang: str) -> str:
    # academic_year_of() คืนปีการศึกษาเป็น พ.ศ.: ภาษาอังกฤษแสดงเป็น ค.ศ. คร่อมสองปี เช่น 2026/2027
    if lang == "en":
        start = buddhist_year - 543
        return TEXT["en"]["academic_year"].format(year=f"{start}/{start + 1}")
    return TEXT["th"]["academic_year"].format(year=buddhist_year)


def year_levels_label(year_levels: list[int] | None, lang: str) -> str:
    if not year_levels:
        return TEXT[lang]["all_years"]
    return TEXT[lang]["year_levels"].format(levels=", ".join(str(level) for level in year_levels))
