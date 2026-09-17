from contextlib import asynccontextmanager
from datetime import date, datetime
from io import BytesIO
import json
from pathlib import Path
from uuid import uuid4
import unicodedata

import pandas as pd
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import (
    Activity,
    ActivityMember,
    ActivitySkill,
    ExternalActivity,
    ExternalActivitySkill,
    Skill,
    Student,
    StudentRequest,
)


STAFF_SKILL_DEFINITIONS = {
    "creative_leadership": "Creative Leadership",
    "innovation": "Innovation",
    "entrepreneurship": "Entrepreneurship",
    "promote_equality": "Promote Equality",
    "academic": "Academic",
    "nature_environmental": "Nature and Environmental",
}

PARTICIPANT_SKILL_DEFINITIONS = {
    "arts_culture_traditions": "Arts, Culture, and Traditions",
    "volunteerism": "Volunteerism",
    "academics": "Academics",
    "internationalization": "Internationalization",
    "health_promotion": "Health Promotion",
    "nature_environmental_conservation": "Nature and Environmental Conservation",
}

SKILL_DEFINITIONS = {
    **STAFF_SKILL_DEFINITIONS,
    **PARTICIPANT_SKILL_DEFINITIONS,
}

# ไฟล์หลักฐานกิจกรรมภายนอก (ไม่ serve แบบ static ต้องผ่าน endpoint)
EXTERNAL_ACTIVITY_UPLOAD_DIR = (
    Path(__file__).resolve().parent
    / "uploads"
    / "external_activities"
)


def seed_skills():
    with SessionLocal() as db:
        changed = False

        for key, label in SKILL_DEFINITIONS.items():
            skill = db.get(Skill, key)

            if not skill:
                db.add(
                    Skill(
                        key=key,
                        label=label,
                    )
                )
                changed = True

        if changed:
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DEV MODE:
    # สร้าง table ถ้ายังไม่มี
    # ภายหลังใช้ Alembic migration แทน create_all
    Base.metadata.create_all(bind=engine)
    seed_skills()
    EXTERNAL_ACTIVITY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    yield


app = FastAPI(
    title="Student Activities API",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Student Activities API",
        "storage": "PostgreSQL",
    }



# ============================================================
# ADMIN DASHBOARD
# ============================================================

DASHBOARD_MONTH_LABELS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]


@app.get("/api/admin/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
):
    """
    Dashboard summary calculated from the same PostgreSQL data
    used by the Activities page.
    """

    total_activities = (
        db.query(func.count(Activity.id))
        .scalar()
        or 0
    )

    total_students = (
        db.query(func.count(Student.student_id))
        .scalar()
        or 0
    )

    # Count unique students that are participants in at least one activity.
    total_participants = (
        db.query(
            func.count(
                func.distinct(ActivityMember.student_id)
            )
        )
        .filter(ActivityMember.role == "participant")
        .scalar()
        or 0
    )

    completed_activities = (
        db.query(func.count(Activity.id))
        .filter(Activity.status == "completed")
        .scalar()
        or 0
    )

    completion_rate = (
        round(
            (completed_activities / total_activities) * 100
        )
        if total_activities
        else 0
    )

    # Activity Growth = activities created in the current year,
    # grouped by created_at month.
    current_year = datetime.now().year
    monthly_counts = [0] * 12

    created_rows = (
        db.query(Activity.created_at)
        .filter(
            func.extract(
                "year",
                Activity.created_at,
            ) == current_year
        )
        .all()
    )

    for (created_at,) in created_rows:
        if created_at is not None:
            monthly_counts[created_at.month - 1] += 1

    activity_growth = [
        {
            "month": month,
            "count": monthly_counts[index],
        }
        for index, month in enumerate(
            DASHBOARD_MONTH_LABELS
        )
    ]

    # "Faculty Skill Distribution" uses Staff skill levels.
    # Level 1-5 is converted to a percentage (20%-100%).
    average_rows = (
        db.query(
            ActivitySkill.skill_key,
            func.avg(ActivitySkill.level),
        )
        .filter(ActivitySkill.target_role == "staff")
        .group_by(ActivitySkill.skill_key)
        .all()
    )

    average_levels = {
        skill_key: float(average_level)
        for skill_key, average_level in average_rows
        if average_level is not None
    }

    skills = []

    for skill_key, label in STAFF_SKILL_DEFINITIONS.items():
        average_level = average_levels.get(skill_key, 0)

        skills.append(
            {
                "name": label,
                "percentage": round(
                    (average_level / 5) * 100
                ),
            }
        )

    return {
        "totalActivities": total_activities,
        "totalStudents": total_students,
        "totalParticipants": total_participants,
        "completionRate": completion_rate,
        "activityGrowth": activity_growth,
        "skills": skills,
        "year": current_year,
    }



# ============================================================
# ADMIN STUDENT SKILLS
# ============================================================


def student_skill_semester_label(value: datetime) -> str:
    """
    Temporary semester derivation because the current database
    does not have an explicit semester/academic-term column.

    Semester 1 = Jan-Jun
    Semester 2 = Jul-Dec
    """
    semester_number = 1 if value.month <= 6 else 2
    return f"Semester {semester_number}/{value.year}"


def student_skill_semester_sort_key(label: str) -> tuple[int, int]:
    try:
        semester_part, year_part = label.replace("Semester ", "").split("/")
        return int(year_part), int(semester_part)
    except (ValueError, AttributeError):
        return (0, 0)


@app.get("/api/admin/student-skills")
def get_admin_student_skills(
    db: Session = Depends(get_db),
):
    """
    Build student proficiency from the real activity data.

    A student's score for each skill is the average participant-skill
    level of activities that the student joined as a participant.
    This avoids inventing a separate student-evaluation table before
    the project has a real evaluation workflow.
    """

    total_students = (
        db.query(func.count(Student.student_id))
        .scalar()
        or 0
    )

    rows = (
        db.query(
            Student.student_id,
            Student.first_name,
            Student.last_name,
            Student.major,
            Activity.start_at,
            ActivitySkill.skill_key,
            ActivitySkill.level,
        )
        .join(
            ActivityMember,
            ActivityMember.student_id == Student.student_id,
        )
        .join(
            Activity,
            Activity.id == ActivityMember.activity_id,
        )
        .join(
            ActivitySkill,
            ActivitySkill.activity_id == Activity.id,
        )
        .filter(
            ActivityMember.role == "participant",
            ActivitySkill.target_role == "participant",
        )
        .all()
    )

    # กิจกรรมภายนอกที่อนุมัติแล้ว (เฉพาะ role participant) นับรวมด้วย
    # ใช้ start_date จัดภาคเรียนเหมือน start_at ของกิจกรรมปกติ
    external_rows = (
        db.query(
            Student.student_id,
            Student.first_name,
            Student.last_name,
            Student.major,
            ExternalActivity.start_date,
            ExternalActivitySkill.skill_key,
            ExternalActivitySkill.level,
        )
        .join(
            ExternalActivity,
            ExternalActivity.student_id == Student.student_id,
        )
        .join(
            ExternalActivitySkill,
            ExternalActivitySkill.external_activity_id == ExternalActivity.id,
        )
        .filter(
            ExternalActivity.status == "approved",
            ExternalActivity.role == "participant",
            ExternalActivitySkill.target_role == "participant",
        )
        .all()
    )

    rows = [*rows, *external_rows]

    # (semester, student_id) -> student data + accumulated skill levels
    grouped: dict[tuple[str, str], dict] = {}

    for (
        student_id,
        first_name,
        last_name,
        major,
        start_at,
        skill_key,
        level,
    ) in rows:
        if start_at is None:
            continue

        if skill_key not in PARTICIPANT_SKILL_DEFINITIONS:
            continue

        semester = student_skill_semester_label(start_at)
        group_key = (semester, student_id)

        if group_key not in grouped:
            grouped[group_key] = {
                "id": student_id,
                "name": f"{first_name} {last_name}".strip(),
                "major": major or "",
                "semester": semester,
                "skill_values": {
                    key: []
                    for key in PARTICIPANT_SKILL_DEFINITIONS
                },
            }

        grouped[group_key]["skill_values"][skill_key].append(
            float(level)
        )

    students = []

    for entry in grouped.values():
        skills = {}

        for skill_key in PARTICIPANT_SKILL_DEFINITIONS:
            values = entry["skill_values"][skill_key]
            # ไม่มี activity ที่ให้ skill นี้กับนักศึกษาคนนี้
            # ให้เป็น None (JSON = null) แทน 0 เพราะ level จริงอยู่ช่วง 1-5
            skills[skill_key] = (
                round(sum(values) / len(values), 2)
                if values
                else None
            )

        students.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "major": entry["major"],
                "semester": entry["semester"],
                "skills": skills,
            }
        )

    students.sort(
        key=lambda item: (
            student_skill_semester_sort_key(item["semester"]),
            item["id"],
        ),
        reverse=True,
    )

    semester_set = {
        item["semester"]
        for item in students
    }

    semesters = sorted(
        semester_set,
        key=student_skill_semester_sort_key,
        reverse=True,
    )

    # Always provide a sensible current semester even before data exists.
    current_semester = student_skill_semester_label(datetime.now())
    if not semesters:
        semesters = [current_semester]

    default_semester = (
        current_semester
        if current_semester in semesters
        else semesters[0]
    )

    total_faculty_by_semester = {
        semester: total_students
        for semester in semesters
    }

    return {
        "semesters": semesters,
        "defaultSemester": default_semester,
        "totalFacultyBySemester": total_faculty_by_semester,
        "benchmarkScores": [4, 4, 4, 4, 4, 4],
        "skillDefinitions": [
            {
                "key": key,
                "label": label,
            }
            for key, label in PARTICIPANT_SKILL_DEFINITIONS.items()
        ],
        "students": students,
    }


# ============================================================
# ACTIVITY
# ============================================================


class ActivityCreate(BaseModel):
    activity_type: str
    name: str

    start_at: datetime
    end_at: datetime

    department: str = ""
    responsible_person: str
    advisor: str = ""
    location: str
    description: str = ""

    # รูปแบบเดียวกับ AdminCreateActivity.vue ปัจจุบัน
    # level = None หมายถึง "ไม่เกี่ยวข้อง" จะไม่ถูกบันทึกลง activity_skills
    staff_skills: dict[str, int | None] = Field(default_factory=dict)
    participant_skills: dict[str, int | None] = Field(default_factory=dict)


class ActivityUpdate(BaseModel):
    name: str | None = None
    activity_type: str | None = None

    start_at: datetime | None = None
    end_at: datetime | None = None

    department: str | None = None
    responsible_person: str | None = None
    advisor: str | None = None
    location: str | None = None
    description: str | None = None

    status: str | None = None

    # ถ้าส่งมา = แทนที่ชุด Skill ของ role นั้นทั้งหมด (level None = ไม่เกี่ยวข้อง)
    staff_skills: dict[str, int | None] | None = None
    participant_skills: dict[str, int | None] | None = None


ACTIVITY_STATUSES = {
    "active",
    "completed",
    "cancelled",
}


def validate_activity_status(status: str):
    if status not in ACTIVITY_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "status ต้องเป็น active, completed หรือ cancelled"
            ),
        )


ACTIVITY_REQUIRED_TEXT_FIELDS = (
    "name",
    "activity_type",
    "responsible_person",
    "location",
)


def validate_required_text(values: dict):
    # ค่าว่างหรือช่องว่างล้วนถือว่าไม่ได้กรอก
    for field_name, value in values.items():
        if value is None or not str(value).strip():
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} ห้ามว่าง",
            )


def validate_skill_levels(
    skills: dict[str, int | None],
    allowed_skills: dict[str, str],
    target_label: str,
):
    for skill_key, level in skills.items():
        if skill_key not in allowed_skills:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Skill '{skill_key}' ไม่ใช่ Skill ของ {target_label}"
                ),
            )

        if level is None:
            continue

        if level < 1 or level > 5:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Skill {skill_key} ต้องอยู่ระหว่าง 1-5"
                ),
            )


def replace_activity_skills(
    db: Session,
    activity_id: int,
    target_role: str,
    skills: dict[str, int | None],
):
    # ลบชุดเดิมของ role นี้แล้วบันทึกใหม่ทั้งชุด
    # skill ที่ level เป็น None (ไม่เกี่ยวข้อง) จะไม่มี row
    db.query(ActivitySkill).filter(
        ActivitySkill.activity_id == activity_id,
        ActivitySkill.target_role == target_role,
    ).delete()

    for skill_key, level in skills.items():
        if level is None:
            continue

        db.add(
            ActivitySkill(
                activity_id=activity_id,
                skill_key=skill_key,
                target_role=target_role,
                level=level,
            )
        )


def get_member_counts(
    db: Session,
    activity_id: int,
) -> tuple[int, int]:
    participant_count = (
        db.query(func.count(ActivityMember.student_id))
        .filter(
            ActivityMember.activity_id == activity_id,
            ActivityMember.role == "participant",
        )
        .scalar()
        or 0
    )

    organizer_count = (
        db.query(func.count(ActivityMember.student_id))
        .filter(
            ActivityMember.activity_id == activity_id,
            ActivityMember.role == "organizer",
        )
        .scalar()
        or 0
    )

    return participant_count, organizer_count


def serialize_activity(
    db: Session,
    activity: Activity,
    include_skills: bool = False,
) -> dict:
    participant_count, organizer_count = get_member_counts(
        db,
        activity.id,
    )

    result = {
        "id": activity.id,
        "uid": activity.uid,
        "activity_type": activity.activity_type,
        "name": activity.name,
        "start_at": activity.start_at,
        "end_at": activity.end_at,
        "department": activity.department,
        "responsible_person": activity.responsible_person,
        "advisor": activity.advisor,
        "location": activity.location,
        "description": activity.description,
        "status": activity.status,
        "created_at": activity.created_at,

        # field สำหรับหน้า Activities ปัจจุบัน
        "organizer": (
            activity.department
            or activity.responsible_person
            or "-"
        ),
        "category": activity.activity_type,
        "date": activity.start_at,
        "participants": participant_count,
        "organizers": organizer_count,
        "capacity": None,
    }

    if include_skills:
        staff_skills = {}
        participant_skills = {}

        for link in activity.skill_levels:
            if link.target_role == "staff":
                staff_skills[link.skill_key] = link.level
            else:
                participant_skills[link.skill_key] = link.level

        result["staff_skills"] = staff_skills
        result["participant_skills"] = participant_skills

    return result


def require_activity(
    db: Session,
    activity_id: int,
) -> Activity:
    activity = db.get(Activity, activity_id)

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบกิจกรรม",
        )

    return activity


@app.get("/api/activities")
def list_activities(
    db: Session = Depends(get_db),
):
    activities = (
        db.query(Activity)
        .order_by(Activity.start_at.asc())
        .all()
    )

    return {
        "total": len(activities),
        "activities": [
            serialize_activity(
                db,
                activity,
                include_skills=True,
            )
            for activity in activities
        ],
    }


@app.post("/api/activities", status_code=201)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
):
    validate_required_text(
        {
            field_name: getattr(payload, field_name)
            for field_name in ACTIVITY_REQUIRED_TEXT_FIELDS
        }
    )

    if payload.end_at <= payload.start_at:
        raise HTTPException(
            status_code=400,
            detail="วัน/เวลาสิ้นสุดต้องอยู่หลังวัน/เวลาเริ่มต้น",
        )

    validate_skill_levels(
        payload.staff_skills,
        STAFF_SKILL_DEFINITIONS,
        "Staff",
    )

    validate_skill_levels(
        payload.participant_skills,
        PARTICIPANT_SKILL_DEFINITIONS,
        "Participant",
    )

    activity = Activity(
        activity_type=payload.activity_type.strip(),
        name=payload.name.strip(),
        start_at=payload.start_at,
        end_at=payload.end_at,
        department=payload.department.strip(),
        responsible_person=payload.responsible_person.strip(),
        advisor=payload.advisor.strip(),
        location=payload.location.strip(),
        description=payload.description.strip(),
        status="active",
    )

    db.add(activity)

    # ขอ id จาก PostgreSQL ก่อนเพื่อสร้าง UID
    db.flush()

    activity.uid = (
        f"SC-{payload.start_at.year}-{activity.id:03d}"
    )

    replace_activity_skills(
        db,
        activity.id,
        "staff",
        payload.staff_skills,
    )

    replace_activity_skills(
        db,
        activity.id,
        "participant",
        payload.participant_skills,
    )

    db.commit()
    db.refresh(activity)

    return serialize_activity(
        db,
        activity,
        include_skills=True,
    )




@app.patch("/api/activities/{activity_id}")
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
):
    activity = require_activity(
        db,
        activity_id,
    )

    updates = payload.model_dump(
        exclude_unset=True,
    )

    if "status" in updates:
        if updates["status"] is None:
            raise HTTPException(
                status_code=400,
                detail="status ห้ามเป็น null",
            )

        validate_activity_status(
            updates["status"],
        )

    new_start_at = (
        updates.get("start_at")
        if updates.get("start_at") is not None
        else activity.start_at
    )

    new_end_at = (
        updates.get("end_at")
        if updates.get("end_at") is not None
        else activity.end_at
    )

    if new_end_at <= new_start_at:
        raise HTTPException(
            status_code=400,
            detail="วัน/เวลาสิ้นสุดต้องอยู่หลังวัน/เวลาเริ่มต้น",
        )

    validate_required_text(
        {
            field_name: updates[field_name]
            for field_name in ACTIVITY_REQUIRED_TEXT_FIELDS
            if field_name in updates
        }
    )

    skill_updates = {
        "staff": updates.pop("staff_skills", None),
        "participant": updates.pop("participant_skills", None),
    }

    if skill_updates["staff"] is not None:
        validate_skill_levels(
            skill_updates["staff"],
            STAFF_SKILL_DEFINITIONS,
            "Staff",
        )

    if skill_updates["participant"] is not None:
        validate_skill_levels(
            skill_updates["participant"],
            PARTICIPANT_SKILL_DEFINITIONS,
            "Participant",
        )

    text_fields = {
        "name",
        "activity_type",
        "department",
        "responsible_person",
        "advisor",
        "location",
        "description",
    }

    for target_role, skills in skill_updates.items():
        if skills is not None:
            replace_activity_skills(
                db,
                activity.id,
                target_role,
                skills,
            )

    for field_name, value in updates.items():
        if field_name in text_fields:
            value = "" if value is None else str(value).strip()

        setattr(
            activity,
            field_name,
            value,
        )

    db.commit()
    db.refresh(activity)

    return serialize_activity(
        db,
        activity,
        include_skills=True,
    )


@app.get("/api/activities/{activity_id}")
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = require_activity(
        db,
        activity_id,
    )

    return serialize_activity(
        db,
        activity,
        include_skills=True,
    )


@app.delete(
    "/api/activities/{activity_id}",
    status_code=204,
)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = require_activity(
        db,
        activity_id,
    )

    db.delete(activity)
    db.commit()

    return None


# ============================================================
# CSV / EXCEL NORMALIZATION
# ============================================================


COLUMN_ALIASES = {
    "รหัสนักศึกษา": "student_id",
    "รหัสนักศึกษษา": "student_id",
    "Student ID": "student_id",
    "student_id": "student_id",
    "student id": "student_id",

    "ชื่อ": "first_name",
    "First Name": "first_name",
    "first_name": "first_name",
    "ชื่อจริง": "first_name", 
    "ชื่อจริง (ไม่ต้องมีคำนำหน้า)": "first_name",
    "first name": "first_name",
    "ชื่อ (ไม่ต้องมีคำนำหน้า)":"first_name",

    "นามสกุล": "last_name",
    "Last Name": "last_name",
    "last_name": "last_name",

    "CMU Email": "email",
    "อีเมล": "email",
    "Email": "email",
    "email": "email",

    "สาขาวิชา": "major",
    "Major": "major",
    "major": "major",

    "Role": "role",
    "role": "role",
}


def normalize_text(text: str) -> str:
    text = str(text)
    text = text.replace("\ufeff", "")
    text = text.replace("\u200b", "")
    text = text.strip()

    return unicodedata.normalize(
        "NFC",
        text,
    )


def normalize_student_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df.columns = [
        normalize_text(column)
        for column in df.columns
    ]

    normalized_aliases = {
        normalize_text(key): value
        for key, value in COLUMN_ALIASES.items()
    }

    rename_map = {}

    for column in df.columns:
        normalized_column = normalize_text(column)

        if normalized_column in normalized_aliases:
            rename_map[column] = (
                normalized_aliases[normalized_column]
            )

    df = df.rename(columns=rename_map)

    required_columns = [
        "student_id",
        "first_name",
        "last_name",
        "email",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=(
                "ไม่พบ column ที่จำเป็น: "
                + ", ".join(missing_columns)
                + f" | column ที่พบ: {list(df.columns)}"
            ),
        )

    keep_columns = required_columns.copy()

    for optional in [
        "faculty",
        "major",
        "role",
    ]:
        if optional in df.columns:
            keep_columns.append(optional)

    df = df[keep_columns].copy()
    df = df.fillna("")

    for column in keep_columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
        )

    if "faculty" not in df.columns:
        df["faculty"] = "Faculty of Science"

    if "major" not in df.columns:
        df["major"] = ""

    if "role" not in df.columns:
        # ถ้าไฟล์ไม่มี column Role ให้เป็น participant อัตโนมัติ
        df["role"] = "participant"
    else:
        # ถ้ามี column Role ให้จัดรูปแบบค่า และถ้าบางแถวว่างให้เป็น participant
        df["role"] = df["role"].str.lower()
        df.loc[
            df["role"].eq(""),
            "role",
        ] = "participant"

    return df


def validate_students(
    df: pd.DataFrame,
) -> list[dict]:
    invalid_rows = []

    for index, row in df.iterrows():
        errors = []

        if not row["student_id"]:
            errors.append("ไม่มีรหัสนักศึกษา")

        if not row["first_name"]:
            errors.append("ไม่มีชื่อ")

        if not row["last_name"]:
            errors.append("ไม่มีนามสกุล")

        if not row["email"]:
            errors.append("ไม่มีอีเมล")
        elif "@" not in row["email"]:
            errors.append(
                "รูปแบบอีเมลไม่ถูกต้อง"
            )

        role = (
            str(row.get("role", "participant"))
            .strip()
            .lower()
        )

        if role not in {
            "participant",
            "organizer",
        }:
            errors.append(
                "Role ต้องเป็น participant หรือ organizer"
            )

        if errors:
            invalid_rows.append(
                {
                    "row": int(index) + 2,
                    "errors": errors,
                }
            )

    return invalid_rows


async def read_student_file(
    file: UploadFile,
) -> dict:
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in {
        ".csv",
        ".xlsx",
    }:
        raise HTTPException(
            status_code=400,
            detail="รองรับเฉพาะไฟล์ .csv และ .xlsx",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์ว่าง",
        )

    try:
        if extension == ".csv":
            df = pd.read_csv(
                BytesIO(contents),
                dtype=str,
            )
        else:
            df = pd.read_excel(
                BytesIO(contents),
                dtype=str,
            )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"ไม่สามารถอ่านไฟล์ได้: {exc}",
        )

    df = normalize_student_columns(df)
    invalid_rows = validate_students(df)

    return {
        "filename": filename,
        "total": len(df),
        "columns": list(df.columns),
        "students": df.to_dict(
            orient="records"
        ),
        "invalid_count": len(invalid_rows),
        "invalid_rows": invalid_rows,
    }


# ============================================================
# PARTICIPANTS
# ============================================================


@app.post(
    "/api/activities/{activity_id}/participants/import/preview"
)
async def preview_activity_participants(
    activity_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    require_activity(
        db,
        activity_id,
    )

    result = await read_student_file(file)

    return {
        "activity_id": activity_id,
        **result,
    }


class ConfirmImportRequest(BaseModel):
    students: list[dict]


def normalize_role(value) -> str:
    role = (
        str(value or "participant")
        .strip()
        .lower()
    )

    if role not in {
        "participant",
        "organizer",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Role ต้องเป็น participant "
                "หรือ organizer"
            ),
        )

    return role


@app.post(
    "/api/activities/{activity_id}/participants/import/confirm"
)
def confirm_activity_participants(
    activity_id: int,
    payload: ConfirmImportRequest,
    db: Session = Depends(get_db),
):
    require_activity(
        db,
        activity_id,
    )

    imported_count = 0
    duplicate_count = 0

    for raw_student in payload.students:
        student_id = str(
            raw_student.get(
                "student_id",
                "",
            )
        ).strip()

        if not student_id:
            raise HTTPException(
                status_code=400,
                detail="พบข้อมูลที่ไม่มี student_id",
            )

        first_name = str(
            raw_student.get(
                "first_name",
                "",
            )
        ).strip()

        last_name = str(
            raw_student.get(
                "last_name",
                "",
            )
        ).strip()

        email = str(
            raw_student.get(
                "email",
                "",
            )
        ).strip()

        faculty = str(
            raw_student.get(
                "faculty",
                "Faculty of Science",
            )
            or "Faculty of Science"
        ).strip()

        major = str(
            raw_student.get(
                "major",
                "",
            )
        ).strip()

        role = normalize_role(
            raw_student.get("role")
        )

        if not first_name or not last_name:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"{student_id}: "
                    "ชื่อ/นามสกุลไม่ครบ"
                ),
            )

        if "@" not in email:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"{student_id}: "
                    "อีเมลไม่ถูกต้อง"
                ),
            )

        # students = master data ของนักศึกษา
        student = db.get(
            Student,
            student_id,
        )

        if not student:
            student = Student(
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                faculty=faculty,
                major=major,
            )

            db.add(student)
            db.flush()
        else:
            # ถ้า import ข้อมูลล่าสุดเข้ามา
            # ให้อัปเดต master data ด้วย
            student.first_name = first_name
            student.last_name = last_name
            student.email = email
            student.faculty = faculty
            student.major = major

        existing_member = db.get(
            ActivityMember,
            (
                activity_id,
                student_id,
            ),
        )

        if existing_member:
            duplicate_count += 1
            continue

        db.add(
            ActivityMember(
                activity_id=activity_id,
                student_id=student_id,
                role=role,
            )
        )

        imported_count += 1

    db.commit()

    total_members = (
        db.query(func.count(ActivityMember.student_id))
        .filter(
            ActivityMember.activity_id
            == activity_id
        )
        .scalar()
        or 0
    )

    return {
        "activity_id": activity_id,
        "imported_count": imported_count,
        "duplicate_count": duplicate_count,
        "total_participants": total_members,
    }


@app.get(
    "/api/activities/{activity_id}/participants"
)
def get_activity_participants(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = require_activity(
        db,
        activity_id,
    )

    rows = (
        db.query(
            ActivityMember,
            Student,
        )
        .join(
            Student,
            Student.student_id
            == ActivityMember.student_id,
        )
        .filter(
            ActivityMember.activity_id
            == activity_id
        )
        .order_by(
            Student.student_id.asc()
        )
        .all()
    )

    students = []

    for member, student in rows:
        students.append(
            {
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "email": student.email,
                "faculty": student.faculty,
                "major": student.major,
                "role": member.role,
            }
        )

    return {
        "activity_id": activity_id,
        "activity": {
            "id": activity.id,
            "uid": activity.uid,
            "name": activity.name,
        },
        "total": len(students),
        "students": students,
    }


class ParticipantUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str
    faculty: str
    major: str
    role: str


@app.patch(
    "/api/activities/{activity_id}/participants/{student_id}"
)
def update_activity_participant(
    activity_id: int,
    student_id: str,
    payload: ParticipantUpdate,
    db: Session = Depends(get_db),
):
    require_activity(
        db,
        activity_id,
    )

    member = db.get(
        ActivityMember,
        (activity_id, student_id),
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบผู้เข้าร่วมนี้ในกิจกรรม",
        )

    student = db.get(Student, student_id)

    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    email = payload.email.strip()
    faculty = payload.faculty.strip()
    major = payload.major.strip()
    role = normalize_role(payload.role)

    if not first_name or not last_name:
        raise HTTPException(
            status_code=400,
            detail="ชื่อ/นามสกุลไม่ครบ",
        )

    if "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="อีเมลไม่ถูกต้อง",
        )

    student.first_name = first_name
    student.last_name = last_name
    student.email = email
    student.faculty = faculty
    student.major = major

    member.role = role

    db.commit()

    return {
        "student_id": student.student_id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "email": student.email,
        "faculty": student.faculty,
        "major": student.major,
        "role": member.role,
    }


# ============================================================
# EXTERNAL ACTIVITIES (ส่งโดยนักศึกษา อนุมัติโดย admin)
# ============================================================


EXTERNAL_ACTIVITY_REQUEST_TYPE = "external_activity"
EXTERNAL_ACTIVITY_REQUEST_LABEL = "External Activity"

EVIDENCE_MAX_BYTES = 5 * 1024 * 1024

# ชนิดไฟล์ตรวจจาก magic bytes จริง ไม่เชื่อ content-type ที่ browser ส่งมา
EVIDENCE_FILE_TYPES = {
    "jpeg": {
        "extensions": {".jpg", ".jpeg"},
        "stored_extension": ".jpg",
        "content_type": "image/jpeg",
    },
    "png": {
        "extensions": {".png"},
        "stored_extension": ".png",
        "content_type": "image/png",
    },
    "pdf": {
        "extensions": {".pdf"},
        "stored_extension": ".pdf",
        "content_type": "application/pdf",
    },
}

# role ของนักศึกษา -> ชุด Skill ที่ admin กำหนดตอนอนุมัติ
EXTERNAL_ROLE_SKILLS = {
    "participant": ("participant", PARTICIPANT_SKILL_DEFINITIONS, "Participant"),
    "organizer": ("staff", STAFF_SKILL_DEFINITIONS, "Staff"),
}

EXTERNAL_ACTIVITY_MAX_LENGTHS = {
    "title": 255,
    "organization": 255,
    "activity_type": 120,
    "location": 255,
}


def get_current_student(
    x_student_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Student:
    # ยังไม่มีระบบ login นักศึกษา: frontend ส่ง student ID จำลองมาใน header
    # เปลี่ยนเป็นอ่านจาก session/token เมื่อมีระบบ login จริง
    student_id = (x_student_id or "").strip()

    if not student_id:
        raise HTTPException(
            status_code=401,
            detail="ไม่พบข้อมูลนักศึกษา (X-Student-Id)",
        )

    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบนักศึกษา",
        )

    return student


def detect_evidence_type(contents: bytes) -> str | None:
    if contents.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    if contents.startswith(b"%PDF-"):
        return "pdf"

    return None


async def read_evidence_file(file: UploadFile) -> dict:
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()

    allowed_extensions = {
        allowed
        for file_type in EVIDENCE_FILE_TYPES.values()
        for allowed in file_type["extensions"]
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์หลักฐานต้องเป็น .jpg, .jpeg, .png หรือ .pdf",
        )

    contents = await file.read(EVIDENCE_MAX_BYTES + 1)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์หลักฐานว่าง",
        )

    if len(contents) > EVIDENCE_MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์หลักฐานต้องมีขนาดไม่เกิน 5MB",
        )

    detected = detect_evidence_type(contents)

    if (
        detected is None
        or extension not in EVIDENCE_FILE_TYPES[detected]["extensions"]
    ):
        raise HTTPException(
            status_code=400,
            detail="เนื้อหาไฟล์ไม่ตรงกับนามสกุลไฟล์ (รองรับ jpg, png, pdf)",
        )

    file_type = EVIDENCE_FILE_TYPES[detected]

    return {
        "contents": contents,
        "original_name": original_name[:255],
        "content_type": file_type["content_type"],
        "stored_name": f"{uuid4().hex}{file_type['stored_extension']}",
    }


def parse_submitted_skills(raw_skills: str, role: str) -> tuple[str, dict]:
    """
    Skill Mapping ที่นักศึกษาตั้งเองตอนส่งฟอร์ม
    multipart ส่ง object ตรง ๆ ไม่ได้ จึงรับเป็น JSON string: {"skill_key": level | null}
    """
    target_role, allowed_skills, target_label = EXTERNAL_ROLE_SKILLS[role]

    try:
        skills = json.loads(raw_skills)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="skills ต้องเป็น JSON object",
        )

    if not isinstance(skills, dict) or any(
        level is not None
        and (isinstance(level, bool) or not isinstance(level, int))
        for level in skills.values()
    ):
        raise HTTPException(
            status_code=400,
            detail="skills ต้องเป็น JSON object ของ skill_key -> level (1-5) หรือ null",
        )

    validate_skill_levels(
        skills,
        allowed_skills,
        target_label,
    )

    related_skills = {
        skill_key: level
        for skill_key, level in skills.items()
        if level is not None
    }

    if not related_skills:
        raise HTTPException(
            status_code=400,
            detail="ต้องกำหนดระดับ Skill ที่เกี่ยวข้องอย่างน้อย 1 รายการ",
        )

    return target_role, related_skills


def external_activity_skills(external_activity: ExternalActivity) -> dict:
    return {
        link.skill_key: link.level
        for link in external_activity.skill_levels
    }


def serialize_external_activity(
    external_activity: ExternalActivity,
) -> dict:
    student = external_activity.student
    target_role = EXTERNAL_ROLE_SKILLS[external_activity.role][0]

    return {
        "id": external_activity.id,
        "student_id": external_activity.student_id,
        "student": {
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "faculty": student.faculty,
            "major": student.major,
        },
        "title": external_activity.title,
        "organization": external_activity.organization,
        "activity_type": external_activity.activity_type,
        "start_date": external_activity.start_date,
        "end_date": external_activity.end_date,
        "location": external_activity.location,
        "role": external_activity.role,
        "description": external_activity.description,
        "status": external_activity.status,
        "reject_reason": external_activity.reject_reason,
        "submitted_at": external_activity.submitted_at,
        "decided_at": external_activity.decided_at,
        "skill_target_role": target_role,
        "skills": external_activity_skills(external_activity),
        "evidence": {
            "original_name": external_activity.evidence_original_name,
            "content_type": external_activity.evidence_content_type,
            "size": external_activity.evidence_size,
            "url": f"/api/external-activities/{external_activity.id}/evidence",
        },
    }


def require_external_activity(
    db: Session,
    external_activity_id: int,
) -> ExternalActivity:
    external_activity = db.get(ExternalActivity, external_activity_id)

    if not external_activity:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบกิจกรรมภายนอกนี้",
        )

    return external_activity


@app.post(
    "/api/student/me/external-activities",
    status_code=201,
)
async def submit_external_activity(
    title: str = Form(...),
    organization: str = Form(...),
    activity_type: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    location: str = Form(...),
    role: str = Form(...),
    description: str = Form(""),
    skills: str = Form(...),
    evidence: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    values = {
        "title": title,
        "organization": organization,
        "activity_type": activity_type,
        "location": location,
    }

    validate_required_text({**values, "role": role})

    for field_name, max_length in EXTERNAL_ACTIVITY_MAX_LENGTHS.items():
        if len(values[field_name].strip()) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} ยาวเกิน {max_length} ตัวอักษร",
            )

    role = role.strip().lower()

    if role not in EXTERNAL_ROLE_SKILLS:
        raise HTTPException(
            status_code=400,
            detail="role ต้องเป็น participant หรือ organizer",
        )

    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="วันที่สิ้นสุดต้องไม่อยู่ก่อนวันที่เริ่มต้น",
        )

    # role participant -> participant skills, organizer -> staff skills
    target_role, related_skills = parse_submitted_skills(skills, role)

    # ตรวจไฟล์เป็นขั้นสุดท้าย และเขียนลงดิสก์หลังข้อมูลอื่นผ่านหมดแล้ว
    evidence_file = await read_evidence_file(evidence)
    evidence_path = EXTERNAL_ACTIVITY_UPLOAD_DIR / evidence_file["stored_name"]
    evidence_path.write_bytes(evidence_file["contents"])

    try:
        external_activity = ExternalActivity(
            student_id=student.student_id,
            title=title.strip(),
            organization=organization.strip(),
            activity_type=activity_type.strip(),
            start_date=start_date,
            end_date=end_date,
            location=location.strip(),
            role=role,
            description=description.strip(),
            evidence_filename=evidence_file["stored_name"],
            evidence_original_name=evidence_file["original_name"],
            evidence_content_type=evidence_file["content_type"],
            evidence_size=len(evidence_file["contents"]),
            status="pending",
            skill_levels=[
                ExternalActivitySkill(
                    skill_key=skill_key,
                    target_role=target_role,
                    level=level,
                )
                for skill_key, level in related_skills.items()
            ],
        )

        db.add(external_activity)
        db.commit()
    except Exception:
        db.rollback()
        evidence_path.unlink(missing_ok=True)
        raise

    db.refresh(external_activity)

    return serialize_external_activity(external_activity)


@app.get("/api/student/me/external-activities")
def list_my_external_activities(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    items = (
        db.query(ExternalActivity)
        .filter(ExternalActivity.student_id == student.student_id)
        .order_by(
            ExternalActivity.submitted_at.desc(),
            ExternalActivity.id.desc(),
        )
        .all()
    )

    return {
        "total": len(items),
        "external_activities": [
            serialize_external_activity(item)
            for item in items
        ],
    }


@app.get("/api/student/me/activities")
def list_my_activities(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    My Activities: กิจกรรมของคณะที่นักศึกษาเป็นสมาชิก
    + กิจกรรมภายนอกที่ได้รับอนุมัติแล้ว
    """

    items = []

    memberships = (
        db.query(ActivityMember, Activity)
        .join(Activity, Activity.id == ActivityMember.activity_id)
        .filter(ActivityMember.student_id == student.student_id)
        .all()
    )

    for member, activity in memberships:
        target_role = (
            "staff"
            if member.role == "organizer"
            else "participant"
        )

        items.append(
            {
                "source": "activity",
                "id": activity.id,
                "title": activity.name,
                "activity_type": activity.activity_type,
                "organizer": (
                    activity.department
                    or activity.responsible_person
                ),
                "start_at": activity.start_at,
                "end_at": activity.end_at,
                "location": activity.location,
                "description": activity.description,
                "role": member.role,
                "status": activity.status,
                "skills": {
                    link.skill_key: link.level
                    for link in activity.skill_levels
                    if link.target_role == target_role
                },
                "evidence_url": None,
            }
        )

    approved_external = (
        db.query(ExternalActivity)
        .filter(
            ExternalActivity.student_id == student.student_id,
            ExternalActivity.status == "approved",
        )
        .all()
    )

    for external_activity in approved_external:
        items.append(
            {
                "source": "external_activity",
                "id": external_activity.id,
                "title": external_activity.title,
                "activity_type": external_activity.activity_type,
                "organizer": external_activity.organization,
                "start_at": datetime.combine(
                    external_activity.start_date,
                    datetime.min.time(),
                ),
                "end_at": datetime.combine(
                    external_activity.end_date,
                    datetime.min.time(),
                ),
                "location": external_activity.location,
                "description": external_activity.description,
                "role": external_activity.role,
                "status": external_activity.status,
                "skills": external_activity_skills(external_activity),
                "evidence_url": (
                    f"/api/external-activities/{external_activity.id}/evidence"
                ),
            }
        )

    items.sort(
        key=lambda item: (item["start_at"], item["source"], item["id"]),
        reverse=True,
    )

    return {
        "student": {
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "faculty": student.faculty,
            "major": student.major,
        },
        "total": len(items),
        "activities": items,
    }


@app.get("/api/external-activities/{external_activity_id}")
def get_external_activity(
    external_activity_id: int,
    db: Session = Depends(get_db),
):
    return serialize_external_activity(
        require_external_activity(db, external_activity_id)
    )


@app.get("/api/external-activities/{external_activity_id}/evidence")
def get_external_activity_evidence(
    external_activity_id: int,
    db: Session = Depends(get_db),
):
    external_activity = require_external_activity(
        db,
        external_activity_id,
    )

    # เก็บเฉพาะชื่อไฟล์ที่ระบบสร้างเอง ใช้ .name กันไม่ให้หลุดออกนอกโฟลเดอร์
    path = (
        EXTERNAL_ACTIVITY_UPLOAD_DIR
        / Path(external_activity.evidence_filename).name
    )

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="ไม่พบไฟล์หลักฐาน",
        )

    return FileResponse(
        path,
        media_type=external_activity.evidence_content_type,
        filename=external_activity.evidence_original_name,
        content_disposition_type="inline",
    )


class ExternalActivityDecision(BaseModel):
    # skill levels นักศึกษาตั้งมาตั้งแต่ตอนส่งแล้ว admin แค่อนุมัติ/ไม่อนุมัติ
    status: str
    reject_reason: str | None = None


@app.patch("/api/external-activities/{external_activity_id}/decision")
def decide_external_activity(
    external_activity_id: int,
    payload: ExternalActivityDecision,
    db: Session = Depends(get_db),
):
    if payload.status not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=400,
            detail="status ต้องเป็น approved หรือ rejected",
        )

    external_activity = require_external_activity(
        db,
        external_activity_id,
    )

    if external_activity.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="กิจกรรมนี้ถูกดำเนินการไปแล้ว",
        )

    if payload.status == "approved":
        external_activity.reject_reason = None
    else:
        reject_reason = (payload.reject_reason or "").strip()

        if not reject_reason:
            raise HTTPException(
                status_code=400,
                detail="กรุณาระบุเหตุผลที่ไม่อนุมัติ",
            )

        external_activity.reject_reason = reject_reason

    external_activity.status = payload.status
    external_activity.decided_at = datetime.now()

    db.commit()
    db.refresh(external_activity)

    return serialize_external_activity(external_activity)


# ============================================================
# STUDENT REQUESTS (Approvals)
# ============================================================


REQUEST_TYPE_DEFINITIONS = {
    "skill_validation": "Skill Validation",
    "special_request": "Special Request",
}


class StudentRequestCreate(BaseModel):
    requester_name: str
    requester_student_id: str
    request_type: str
    detail: str = ""


class RequestDecision(BaseModel):
    status: str


def serialize_request(request: StudentRequest) -> dict:
    return {
        "id": request.id,
        "source": "student_request",
        "requester_name": request.requester_name,
        "requester_student_id": request.requester_student_id,
        "request_type": request.request_type,
        "request_type_label": REQUEST_TYPE_DEFINITIONS.get(
            request.request_type,
            request.request_type,
        ),
        "detail": request.detail,
        "status": request.status,
        "submitted_at": request.submitted_at,
        "decided_at": request.decided_at,
    }


@app.get("/api/requests/stats")
def get_request_stats(
    db: Session = Depends(get_db),
):
    today_start = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    total_pending = (
        db.query(func.count(StudentRequest.id))
        .filter(StudentRequest.status == "pending")
        .scalar()
        or 0
    )

    approved_today = (
        db.query(func.count(StudentRequest.id))
        .filter(
            StudentRequest.status == "approved",
            StudentRequest.decided_at >= today_start,
        )
        .scalar()
        or 0
    )

    rejected_today = (
        db.query(func.count(StudentRequest.id))
        .filter(
            StudentRequest.status == "rejected",
            StudentRequest.decided_at >= today_start,
        )
        .scalar()
        or 0
    )

    # รวมกิจกรรมภายนอกเข้าไปในตัวเลขของหน้า Approvals ด้วย
    total_pending += (
        db.query(func.count(ExternalActivity.id))
        .filter(ExternalActivity.status == "pending")
        .scalar()
        or 0
    )

    approved_today += (
        db.query(func.count(ExternalActivity.id))
        .filter(
            ExternalActivity.status == "approved",
            ExternalActivity.decided_at >= today_start,
        )
        .scalar()
        or 0
    )

    rejected_today += (
        db.query(func.count(ExternalActivity.id))
        .filter(
            ExternalActivity.status == "rejected",
            ExternalActivity.decided_at >= today_start,
        )
        .scalar()
        or 0
    )

    return {
        "total_pending": total_pending,
        "approved_today": approved_today,
        "rejected_today": rejected_today,
    }


def serialize_external_request(
    external_activity: ExternalActivity,
) -> dict:
    student = external_activity.student

    return {
        "id": external_activity.id,
        "source": EXTERNAL_ACTIVITY_REQUEST_TYPE,
        "requester_name": f"{student.first_name} {student.last_name}".strip(),
        "requester_student_id": external_activity.student_id,
        "request_type": EXTERNAL_ACTIVITY_REQUEST_TYPE,
        "request_type_label": EXTERNAL_ACTIVITY_REQUEST_LABEL,
        "detail": external_activity.title,
        "status": external_activity.status,
        "submitted_at": external_activity.submitted_at,
        "decided_at": external_activity.decided_at,
    }


@app.get("/api/requests")
def list_requests(
    status: str | None = "pending",
    request_type: str | None = None,
    sort: str = "date_desc",
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
):
    # รวม 2 แหล่ง (student_requests + external_activities) แล้วเรียง/แบ่งหน้าใน Python
    # ปริมาณคำขอยังน้อย ถ้าเยอะขึ้นควรย้ายไปทำ UNION ใน SQL
    include_student_requests = (
        not request_type
        or request_type != EXTERNAL_ACTIVITY_REQUEST_TYPE
    )
    include_external = (
        not request_type
        or request_type == EXTERNAL_ACTIVITY_REQUEST_TYPE
    )

    items = []

    if include_student_requests:
        query = db.query(StudentRequest)

        if status:
            query = query.filter(StudentRequest.status == status)

        if request_type:
            query = query.filter(StudentRequest.request_type == request_type)

        items.extend(serialize_request(item) for item in query.all())

    if include_external:
        query = db.query(ExternalActivity)

        if status:
            query = query.filter(ExternalActivity.status == status)

        items.extend(serialize_external_request(item) for item in query.all())

    items.sort(
        key=lambda item: (item["submitted_at"], item["source"], item["id"]),
        reverse=sort != "date_asc",
    )

    total = len(items)

    page = max(page, 1)
    page_size = max(1, min(page_size, 100))
    start = (page - 1) * page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "requests": items[start:start + page_size],
    }


@app.post("/api/requests", status_code=201)
def create_request(
    payload: StudentRequestCreate,
    db: Session = Depends(get_db),
):
    validate_required_text(
        {
            "requester_name": payload.requester_name,
            "requester_student_id": payload.requester_student_id,
        }
    )

    if payload.request_type not in REQUEST_TYPE_DEFINITIONS:
        raise HTTPException(
            status_code=400,
            detail="request_type ไม่ถูกต้อง",
        )

    request = StudentRequest(
        requester_name=payload.requester_name.strip(),
        requester_student_id=payload.requester_student_id.strip(),
        request_type=payload.request_type,
        detail=payload.detail.strip(),
        status="pending",
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return serialize_request(request)


@app.patch("/api/requests/{request_id}")
def decide_request(
    request_id: int,
    payload: RequestDecision,
    db: Session = Depends(get_db),
):
    if payload.status not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=400,
            detail="status ต้องเป็น approved หรือ rejected",
        )

    request = db.get(StudentRequest, request_id)

    if not request:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบคำขอนี้",
        )

    if request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="คำขอนี้ถูกดำเนินการไปแล้ว",
        )

    request.status = payload.status
    request.decided_at = datetime.now()

    db.commit()
    db.refresh(request)

    return serialize_request(request)
