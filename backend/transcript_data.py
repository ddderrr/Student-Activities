"""ข้อมูลของ Transcript: ชั้นปี ปีการศึกษา และรายการกิจกรรมตามตัวกรอง (ไม่ผูกกับรูปแบบ PDF)

- ชั้นปีคิดจากรหัสนักศึกษา มช. 9 หลัก: 2 หลักแรก = ปีที่เข้า (พ.ศ. 25xx)
  รหัสไม่ตรงรูปแบบ = ไม่รู้ชั้นปี เลือกได้แค่ "ทุกชั้นปี"
- ชั้นปีที่ 1 = ปีการศึกษาที่เข้า, ชั้นปีที่ 2 = ปีการศึกษาถัดไป ...
- ปีการศึกษาของกิจกรรมคิดจากวันที่จัด (เริ่มเดือน ACADEMIC_YEAR_START_MONTH)
- นับเฉพาะกิจกรรมของคณะที่ไม่ถูกยกเลิก และกิจกรรมภายนอกที่อนุมัติแล้ว
- คะแนนทักษะคิดจากกิจกรรมที่เลือกเท่านั้น (บทบาทผู้เข้าร่วม เหมือนหน้า My Skills)
"""

import re
from datetime import date, datetime

from sqlalchemy.orm import Session

import transcript_config
from models import (
    Activity,
    ActivityMember,
    ActivitySkill,
    ExternalActivity,
    ExternalActivitySkill,
    Student,
)
from skill_definitions import PARTICIPANT_SKILL_DEFINITIONS


STUDENT_ID_PATTERN = re.compile(r"^(\d{2})\d{7}$")

SCOPE_LABELS = {
    "all": "กิจกรรมทั้งหมด",
    "major": "เฉพาะกิจกรรมของสาขา",
    "faculty": "เฉพาะกิจกรรมส่วนกลางของคณะ",
    "external": "เฉพาะกิจกรรมภายนอก",
}

# scope -> source ของกิจกรรมที่นับ (None = ทุก source)
SCOPE_SOURCES = {
    "all": None,
    "major": {"major"},
    "faculty": {"faculty"},
    "external": {"external"},
}

SOURCE_KEYS = ("faculty", "major", "other_major", "external")

ROLE_LABELS = {
    "participant": "ผู้เข้าร่วม",
    "organizer": "ผู้จัด / ทีมงาน",
}

SKILL_LABELS_TH = {
    "arts_culture_traditions": "ศิลปะ วัฒนธรรม และประเพณี",
    "volunteerism": "จิตอาสาและการมีส่วนร่วมเพื่อสังคม",
    "academics": "การเรียนรู้และพัฒนาทางวิชาการ",
    "internationalization": "ความเป็นสากลและการเรียนรู้ข้ามวัฒนธรรม",
    "health_promotion": "การส่งเสริมสุขภาพและความเป็นอยู่ที่ดี",
    "nature_environmental_conservation": "การอนุรักษ์ธรรมชาติและสิ่งแวดล้อม",
}


def today() -> date:
    # แยกเป็นฟังก์ชันเพื่อให้เทสต์กำหนดวันที่ได้
    return date.today()


# ------------------------------------------------------------
# ชั้นปี / ปีการศึกษา
# ------------------------------------------------------------


def entry_year_from_student_id(student_id: str | None) -> int | None:
    match = STUDENT_ID_PATTERN.match((student_id or "").strip())
    return 2500 + int(match.group(1)) if match else None


def academic_year_of(value: date | datetime) -> int:
    """ปีการศึกษา (พ.ศ.) ของวันที่"""
    day = value.date() if isinstance(value, datetime) else value
    buddhist_year = day.year + 543

    if day.month >= transcript_config.ACADEMIC_YEAR_START_MONTH:
        return buddhist_year

    return buddhist_year - 1


def year_level_for(entry_year: int | None, academic_year: int) -> int | None:
    if entry_year is None:
        return None

    level = academic_year - entry_year + 1
    return level if level >= 1 else None


def current_year_level(student_id: str | None, on: date | None = None) -> int | None:
    return year_level_for(
        entry_year_from_student_id(student_id),
        academic_year_of(on or today()),
    )


def allowed_year_levels(student_id: str | None) -> list[int]:
    level = current_year_level(student_id)
    return list(range(1, level + 1)) if level else []


def validate_year_levels(
    student_id: str | None,
    year_levels: list[int] | None,
) -> list[int] | None:
    """None/ว่าง = ทุกชั้นปี, ชั้นปีที่เลือกต้องอยู่ระหว่าง 1 ถึงชั้นปีปัจจุบัน"""
    if not year_levels:
        return None

    allowed = allowed_year_levels(student_id)

    if not allowed:
        raise ValueError("ไม่ทราบชั้นปีจากรหัสนักศึกษา เลือกได้เฉพาะทุกชั้นปี")

    invalid = sorted(set(year_levels) - set(allowed))

    if invalid:
        raise ValueError(
            f"เลือกชั้นปีได้ตั้งแต่ปี 1 ถึงปี {allowed[-1]} "
            f"(ชั้นปีที่ไม่ถูกต้อง: {', '.join(map(str, invalid))})"
        )

    return sorted(set(year_levels))


# ------------------------------------------------------------
# รายการกิจกรรม
# ------------------------------------------------------------


def internal_source(activity_owner: str | None, student_major: str) -> str:
    owner = (activity_owner or "").strip()

    if not owner:
        return "faculty"

    return "major" if student_major and owner == student_major else "other_major"


def load_internal_items(db: Session, student: Student) -> list[dict]:
    student_major = (student.major or "").strip()

    rows = (
        db.query(Activity, ActivityMember.role)
        .join(ActivityMember, ActivityMember.activity_id == Activity.id)
        .filter(
            ActivityMember.student_id == student.student_id,
            Activity.status != "cancelled",
        )
        .all()
    )

    activity_ids = [activity.id for activity, _ in rows]
    skill_rows = (
        db.query(ActivitySkill)
        .filter(
            ActivitySkill.activity_id.in_(activity_ids),
            ActivitySkill.target_role == "participant",
        )
        .all()
        if activity_ids
        else []
    )

    skills_by_activity: dict[int, dict[str, int]] = {}
    for link in skill_rows:
        skills_by_activity.setdefault(link.activity_id, {})[link.skill_key] = link.level

    items = []
    for activity, role in rows:
        source = internal_source(activity.major, student_major)

        items.append(
            {
                "key": f"activity-{activity.id}",
                "title": activity.name,
                "activity_type": activity.activity_type,
                "organizer": (
                    f"สาขา{activity.major}"
                    if activity.major
                    else activity.department or transcript_config.FACULTY_NAME
                ),
                "date": activity.start_at.date(),
                "role": role,
                "source": source,
                # ทักษะผู้เข้าร่วม นับเฉพาะตอนเป็นผู้เข้าร่วม
                "skills": skills_by_activity.get(activity.id, {}) if role == "participant" else {},
            }
        )

    return items


def load_external_items(db: Session, student: Student) -> list[dict]:
    activities = (
        db.query(ExternalActivity)
        .filter(
            ExternalActivity.student_id == student.student_id,
            ExternalActivity.status == "approved",
        )
        .all()
    )

    activity_ids = [activity.id for activity in activities]
    skill_rows = (
        db.query(ExternalActivitySkill)
        .filter(
            ExternalActivitySkill.external_activity_id.in_(activity_ids),
            ExternalActivitySkill.target_role == "participant",
        )
        .all()
        if activity_ids
        else []
    )

    skills_by_activity: dict[int, dict[str, int]] = {}
    for link in skill_rows:
        skills_by_activity.setdefault(link.external_activity_id, {})[link.skill_key] = link.level

    return [
        {
            "key": f"external-{activity.id}",
            "title": activity.title,
            "activity_type": activity.activity_type,
            "organizer": activity.organization,
            "date": activity.start_date,
            "role": activity.role,
            "source": "external",
            "skills": (
                skills_by_activity.get(activity.id, {})
                if activity.role == "participant"
                else {}
            ),
        }
        for activity in activities
    ]


def source_label(item: dict) -> str:
    if item["source"] == "external":
        return "กิจกรรมภายนอก"

    if item["source"] == "faculty":
        return "กิจกรรมคณะ"

    return "กิจกรรมสาขา"


def average_skills(items: list[dict]) -> dict[str, float | None]:
    values: dict[str, list[int]] = {key: [] for key in PARTICIPANT_SKILL_DEFINITIONS}

    for item in items:
        for skill_key, level in item["skills"].items():
            if skill_key in values:
                values[skill_key].append(level)

    return {
        key: round(sum(levels) / len(levels), 2) if levels else None
        for key, levels in values.items()
    }


def collect_transcript(
    db: Session,
    student: Student,
    scope: str = "all",
    year_levels: list[int] | None = None,
) -> dict:
    if scope not in SCOPE_SOURCES:
        raise ValueError(f"scope ต้องเป็น {', '.join(SCOPE_SOURCES)}")

    selected_levels = validate_year_levels(student.student_id, year_levels)
    entry_year = entry_year_from_student_id(student.student_id)
    sources = SCOPE_SOURCES[scope]

    items = []
    for item in load_internal_items(db, student) + load_external_items(db, student):
        if sources is not None and item["source"] not in sources:
            continue

        item["academic_year"] = academic_year_of(item["date"])
        item["year_level"] = year_level_for(entry_year, item["academic_year"])

        if selected_levels is not None and item["year_level"] not in selected_levels:
            continue

        item["role_label"] = ROLE_LABELS.get(item["role"], item["role"])
        item["source_label"] = source_label(item)
        items.append(item)

    items.sort(key=lambda item: (item["date"], item["title"]))

    groups = []
    for item in items:
        if not groups or groups[-1]["academic_year"] != item["academic_year"]:
            groups.append(
                {
                    "academic_year": item["academic_year"],
                    "year_level": item["year_level"],
                    "activities": [],
                }
            )
        groups[-1]["activities"].append(item)

    skills = average_skills(items)

    return {
        "student": {
            "student_id": student.student_id,
            "name": f"{student.first_name} {student.last_name}".strip(),
            "major": (student.major or "").strip(),
            "faculty": transcript_config.FACULTY_NAME,
            "year_level": current_year_level(student.student_id),
        },
        "filters": {
            "scope": scope,
            "scope_label": SCOPE_LABELS[scope],
            "year_levels": selected_levels,
        },
        "groups": groups,
        "summary": {
            "total": len(items),
            "by_source": {
                key: sum(1 for item in items if item["source"] == key)
                for key in SOURCE_KEYS
            },
            "participant": sum(1 for item in items if item["role"] == "participant"),
            "organizer": sum(1 for item in items if item["role"] != "participant"),
        },
        "skills": skills,
        "skill_rows": [
            {
                "key": key,
                "label": label,
                "label_th": SKILL_LABELS_TH.get(key, label),
                "score": skills[key],
            }
            for key, label in PARTICIPANT_SKILL_DEFINITIONS.items()
        ],
    }


def scope_counts(db: Session, student: Student) -> dict[str, int]:
    return {
        scope: collect_transcript(db, student, scope=scope)["summary"]["total"]
        for scope in SCOPE_SOURCES
    }
