from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
import unicodedata

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import (
    Activity,
    ActivityMember,
    ActivitySkill,
    Skill,
    Student,
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
    staff_skills: dict[str, int] = Field(default_factory=dict)
    participant_skills: dict[str, int] = Field(default_factory=dict)


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


def validate_skill_levels(
    skills: dict[str, int],
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

        if level < 1 or level > 5:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Skill {skill_key} ต้องอยู่ระหว่าง 1-5"
                ),
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
            serialize_activity(db, activity)
            for activity in activities
        ],
    }


@app.post("/api/activities", status_code=201)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
):
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

    for skill_key, level in payload.staff_skills.items():
        db.add(
            ActivitySkill(
                activity_id=activity.id,
                skill_key=skill_key,
                target_role="staff",
                level=level,
            )
        )

    for skill_key, level in payload.participant_skills.items():
        db.add(
            ActivitySkill(
                activity_id=activity.id,
                skill_key=skill_key,
                target_role="participant",
                level=level,
            )
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

    required_text_fields = {
        "name",
        "activity_type",
        "responsible_person",
        "location",
    }

    for field_name in required_text_fields:
        if field_name in updates:
            value = updates[field_name]

            if value is None or not str(value).strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"{field_name} ห้ามว่าง",
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

    "ชื่อ": "first_name",
    "First Name": "first_name",
    "first_name": "first_name",

    "นามสกุล": "last_name",
    "Last Name": "last_name",
    "last_name": "last_name",

    "CMU Email": "email",
    "อีเมล": "email",
    "Email": "email",
    "email": "email",

    "คณะ": "faculty",
    "Faculty": "faculty",
    "faculty": "faculty",

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
        df["role"] = "participant"
    else:
        # ถ้ามี column Role แต่บางแถวว่าง
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
