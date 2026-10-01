from contextlib import asynccontextmanager
from datetime import date, datetime
from io import BytesIO, StringIO
import json
import math
from pathlib import Path
import shutil
from uuid import uuid4
import unicodedata
from xml.sax.saxutils import escape as xml_escape

import openpyxl
import openpyxl.styles
import pandas as pd
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, String
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from admin_auth import (
    AdminContext,
    get_current_admin,
    get_optional_admin,
    is_admin_bypass_enabled,
    list_bypass_admins,
    require_central_admin,
)
from admin_scope import (
    can_access_student,
    ensure_can_access_activity,
    ensure_can_access_student,
    ensure_can_assign_major,
    resolve_branch_filter,
    scope_activity_query,
    scope_external_activity_query,
    scope_student_query,
    scope_student_request_query,
)
import academic_calendar
from database import Base, SessionLocal, engine, get_db
from faculty_utils import normalize_faculty
from import_limits import (
    MAX_IMPORT_ROWS,
    ensure_import_file_within_limits,
    read_import_upload,
)
import transcript_data
from transcript_pdf import STYLES as TRANSCRIPT_STYLES, render_transcript_pdf
from skill_scoring import (
    activity_source,
    average_activity_skills,
    average_skill_levels,
    counted_activity_filter,
    counted_external_activity_filter,
    faculty_activity_filter,
    round_half_up,
    skill_levels_from_activities,
    major_activity_filter,
    student_first_average,
)
from skill_definitions import (
    PARTICIPANT_SKILL_DEFINITIONS,
    SKILL_DEFINITIONS,
    STAFF_SKILL_DEFINITIONS,
)
from student_bypass import STUDENT_LOGIN_ACCOUNTS, STUDENT_MOCK_PASSWORD
from models import (
    Activity,
    ActivityMember,
    ActivitySkill,
    ExternalActivity,
    ExternalActivityEvidence,
    ExternalActivitySkill,
    Notification,
    Skill,
    Student,
    StudentRequest,
    StudentSkillBenchmark,
)



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
    # ให้ frontend อ่านชื่อไฟล์ตอนดาวน์โหลด PDF ได้
    expose_headers=["Content-Disposition"],
)


@app.get("/")
def home():
    return {
        "message": "Student Activities API",
        "storage": "PostgreSQL",
    }


# ============================================================
# ADMIN AUTH (bypass สำหรับพัฒนา ดู admin_auth.py)
# ============================================================


def serialize_admin(admin: AdminContext) -> dict:
    return {
        "email": admin.email,
        "name": admin.name,
        "major": admin.major,
        "is_central": admin.is_central,
    }


@app.get("/api/admin/auth/bypass")
def get_admin_bypass_status():
    # หน้า login ฝั่ง admin ใช้แสดงรายชื่อให้เลือก และบอกว่า bypass ปิดอยู่หรือไม่
    if not is_admin_bypass_enabled():
        return {"enabled": False, "accounts": []}

    return {
        "enabled": True,
        "accounts": [serialize_admin(admin) for admin in list_bypass_admins()],
    }


@app.get("/api/admin/me")
def get_admin_me(
    admin: AdminContext = Depends(get_current_admin),
):
    return serialize_admin(admin)


# ============================================================
# STUDENT AUTH (bypass สำหรับพัฒนา ดู student_bypass.py)
# ============================================================


def serialize_student_account(student: Student) -> dict:
    return {
        "student_id": student.student_id,
        "email": student.email,
        "name": f"{student.first_name} {student.last_name}".strip(),
        "major": student.major,
        "faculty": student.faculty,
    }


class StudentLoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/student/auth/login")
def login_student(payload: StudentLoginRequest, db: Session = Depends(get_db)):
    # MOCK LOGIN (dev): ทุกบัญชีใช้รหัสผ่านร่วมค่าเดียว (STUDENT_MOCK_PASSWORD)
    # -- เปลี่ยนเป็นตรวจกับระบบยืนยันตัวตนจริงเมื่อมี
    email = payload.email.strip().lower()

    if not email or not payload.password:
        raise HTTPException(status_code=400, detail="กรุณากรอกอีเมลและรหัสผ่าน")

    # อีเมล mock ที่ใช้ร่วมกันทั้งสาขา ระบุคนไว้ใน STUDENT_LOGIN_ACCOUNTS
    # อีเมลอื่น (เช่นนักศึกษาที่นำเข้าจากหน้า Settings) ค้นจากตาราง students
    student_id = STUDENT_LOGIN_ACCOUNTS.get(email)

    if student_id is not None:
        student = db.get(Student, student_id)
    else:
        student = (
            db.query(Student)
            .filter(func.lower(func.trim(Student.email)) == email)
            .order_by(Student.student_id)
            .first()
        )

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบอีเมลนี้ในระบบ")

    if payload.password != STUDENT_MOCK_PASSWORD:
        raise HTTPException(status_code=401, detail="รหัสผ่านไม่ถูกต้อง")

    return serialize_student_account(student)


# ============================================================
# ADMIN DASHBOARD
# ============================================================

DASHBOARD_MONTH_LABELS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]


def dashboard_semester_months(semester: str) -> list[int]:
    """Return PostgreSQL month numbers (1-12) for the selected semester."""
    normalized = (semester or "ALL").strip().upper()

    if normalized == "SEMESTER_1":
        return [1, 2, 3, 4, 5, 6]
    if normalized == "SEMESTER_2":
        return [7, 8, 9, 10, 11, 12]
    return list(range(1, 13))


def parse_dashboard_months(semester: str, months: str | None) -> list[int]:
    """เดือนของช่วงที่เลือกใน Dashboard: months (เช่น "7,8,9") ถ้ามี ไม่งั้นทั้งภาคเรียน"""
    if not months:
        return dashboard_semester_months(semester)

    try:
        selected_months = sorted(
            {int(item) for item in months.split(",") if item.strip()}
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="months ต้องเป็นตัวเลข 1-12 คั่นด้วย comma",
        )

    if not selected_months or any(
        month < 1 or month > 12 for month in selected_months
    ):
        raise HTTPException(
            status_code=400,
            detail="months ต้องอยู่ระหว่าง 1-12",
        )

    return selected_months


def dashboard_effective_completed(activity: Activity, now_value: datetime) -> bool:
    """
    Dashboard completion rule:
    - cancelled is never completed
    - explicit completed is completed
    - an active activity whose end_at has passed is treated as completed automatically

    This is derived for reporting; it does not silently rewrite the database row.
    """
    if activity.status == "cancelled":
        return False
    if activity.status == "completed":
        return True
    return activity.end_at is not None and activity.end_at < now_value


@app.get("/api/admin/dashboard")
def get_admin_dashboard(
    year: int | None = None,
    semester: str = "ALL",
    months: str | None = None,
    major: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    """
    Dashboard summary for the selected activity year/semester.

    "กิจกรรม" (Activities) here means faculty activities (Activity) only --
    the same set GET /api/activities (owned_only=true) returns -- so the KPI
    count, participants, completion rate and Activity Growth chart all agree
    with the Activities page. Approved external activities that students
    submit themselves are a separate concept (reviewed via Approvals / a
    student's own history) and are intentionally NOT folded into these
    numbers, since silently merging them in previously made the Dashboard
    disagree with the Activities list for the same admin.

    Student count remains the faculty/system total because students are
    master data, not activities -- see totalStudents vs totalParticipants
    below.

    แอดมินสาขา: นักศึกษา ผู้เข้าร่วม และกิจกรรมของคณะ (Activity) นับเฉพาะของ
    สาขาตัวเอง (owned_only: ไม่รวมกิจกรรมที่ยังไม่มีเจ้าของ major=None)

    `months`: optional comma-separated month numbers (e.g. "9" or "7,8,9")
    that narrows the period further than `semester` — used when the admin
    clicks a single month/quarter in the Activity Growth chart instead of
    just picking a semester.

    `major`: แอดมินกลางเลือก filter สาขาได้จากหน้า Dashboard (แอดมินสาขาไม่มี
    ผลจาก param นี้ เพราะถูก scope ตามสาขาตัวเองอยู่แล้ว)
    """
    admin = resolve_branch_filter(admin, major)
    now_value = datetime.now()
    selected_year = year or now_value.year

    selected_months = parse_dashboard_months(semester, months)

    # Activities are filtered by the real activity date (start_at), not created_at.
    # Cancelled activities never happened, so no KPI or chart counts them.
    # สถิติ Dashboard ของแอดมินสาขา นับเฉพาะกิจกรรมที่เป็นของสาขาตัวเองจริง ๆ
    # (include_unowned=False) กิจกรรมที่ยังไม่มีเจ้าของไม่ควรถูกนับเป็นสถิติ
    # ของสาขาไหนสาขาหนึ่ง -- ต่างจากหน้ารายการกิจกรรม (list_activities) ที่ยัง
    # ให้แอดมินสาขาเห็น/จัดการกิจกรรมที่ยังไม่มีเจ้าของได้ตามเดิม
    period_activities = (
        scope_activity_query(db.query(Activity), admin, include_unowned=False)
        .filter(
            counted_activity_filter(),
            func.extract("year", Activity.start_at) == selected_year,
            func.extract("month", Activity.start_at).in_(selected_months),
        )
        .all()
    )

    # "กิจกรรม" ในหน้า Dashboard หมายถึงกิจกรรมของคณะ (Activity) เท่านั้น --
    # ไม่รวมกิจกรรมภายนอกที่นักศึกษายื่นเอง (ExternalActivity) แม้จะอนุมัติแล้ว
    # ก็ตาม เพื่อให้ตัวเลขตรงกับหน้า Activities list (GET /api/activities) และ
    # กราฟ/skill distribution ที่คำนวณจากชุดข้อมูลเดียวกันฝั่ง frontend --
    # กิจกรรมภายนอกยังดูได้ตามปกติผ่านหน้า Approvals/ประวัติของนักศึกษาแต่ละคน
    total_activities = len(period_activities)
    period_activity_ids = [activity.id for activity in period_activities]

    total_students = (
        scope_student_query(db.query(func.count(Student.student_id)), admin)
        .scalar()
        or 0
    )

    # ผู้เข้าร่วม = นักศึกษาที่มีบทบาท participant ในกิจกรรมของคณะช่วงที่เลือก
    # (นิยามเดียวกับ "กิจกรรม" ด้านบน ไม่รวมกิจกรรมภายนอก)
    internal_participant_ids = set()

    if period_activity_ids:
        internal_participant_ids = {
            row[0]
            for row in (
                scope_student_query(
                    db.query(ActivityMember.student_id)
                    .join(Student, Student.student_id == ActivityMember.student_id)
                    .filter(
                        ActivityMember.role == "participant",
                        ActivityMember.activity_id.in_(period_activity_ids),
                    ),
                    admin,
                )
                .distinct()
                .all()
            )
        }

    total_participants = len(internal_participant_ids)

    # period_activities already excludes cancelled activities.
    completion_eligible = period_activities
    completed_activities = sum(
        1
        for activity in completion_eligible
        if dashboard_effective_completed(activity, now_value)
    )

    completion_rate = (
        round((completed_activities / len(completion_eligible)) * 100)
        if completion_eligible
        else 0
    )

    # Activity Growth uses start_at and the selected year/semester. เฉพาะกิจกรรม
    # ของคณะ (ไม่รวมกิจกรรมภายนอก) นิยามเดียวกับ total_activities ด้านบน
    monthly_counts = [0] * 12
    for activity in period_activities:
        if activity.start_at is not None:
            monthly_counts[activity.start_at.month - 1] += 1

    activity_growth = [
        {
            "month": DASHBOARD_MONTH_LABELS[index],
            "count": monthly_counts[index],
        }
        for index in range(12)
        if (index + 1) in selected_months
    ]

    # Keep this payload for backward compatibility. The current Vue page
    # calculates period/role Skill Distribution from activity detail data.
    average_rows = (
        scope_activity_query(
            db.query(
                ActivitySkill.skill_key,
                func.avg(ActivitySkill.level),
            ).join(Activity, Activity.id == ActivitySkill.activity_id),
            admin,
            include_unowned=False,
        )
        .filter(
            ActivitySkill.target_role == "staff",
            counted_activity_filter(),
            func.extract("year", Activity.start_at) == selected_year,
            func.extract("month", Activity.start_at).in_(selected_months),
        )
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
        average_level = average_levels.get(skill_key)
        skills.append(
            {
                "name": label,
                "percentage": (
                    round((average_level / 5) * 100)
                    if average_level is not None
                    else 0
                ),
            }
        )

    available_year_rows = (
        scope_activity_query(
            db.query(func.extract("year", Activity.start_at)),
            admin,
            include_unowned=False,
        )
        .filter(counted_activity_filter())
        .distinct()
        .order_by(func.extract("year", Activity.start_at).desc())
        .all()
    )
    available_years = [
        int(value)
        for (value,) in available_year_rows
        if value is not None
    ]
    if now_value.year not in available_years:
        available_years.append(now_value.year)
        available_years.sort(reverse=True)

    return {
        "totalActivities": total_activities,
        "totalStudents": total_students,
        "totalParticipants": total_participants,
        "completedActivities": completed_activities,
        "completionEligibleActivities": len(completion_eligible),
        "completionRate": completion_rate,
        "activityGrowth": activity_growth,
        "skills": skills,
        "year": selected_year,
        "semester": semester,
        "availableYears": available_years,
    }


@app.get("/api/admin/dashboard/skill-distribution")
def get_dashboard_skill_distribution(
    year: int | None = None,
    semester: str = "ALL",
    months: str | None = None,
    major: str | None = None,
    track: str = "participant",
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    """
    กราฟ Skill Distribution ของหน้า Dashboard

    - กิจกรรมของคณะตามขอบเขตเดียวกับ KPI (include_unowned=False) ไม่รวมกิจกรรมภายนอก
    - ไม่นับกิจกรรม cancelled (counted_activity_filter)
    - ช่วงเวลา: year + months ถ้ามี ไม่งั้นทั้ง semester (เหมือน /api/admin/dashboard)
    - เฉลี่ยตามกิจกรรม: แต่ละกิจกรรมน้ำหนักเท่ากัน ไม่ขึ้นกับจำนวนผู้เข้าร่วม
      percentage = ค่าเฉลี่ย / 5 x 100 ปัดครึ่งขึ้น (ตัวเลขเดียวกับที่หน้าเว็บเคยคำนวณเอง)
    """
    if track not in SKILL_TRACKS:
        raise HTTPException(status_code=400, detail="track ต้องเป็น participant หรือ staff")

    admin = resolve_branch_filter(admin, major)
    selected_year = year or datetime.now().year
    selected_months = parse_dashboard_months(semester, months)
    target_role = SKILL_TRACKS[track]["target_role"]
    definitions = SKILL_TRACKS[track]["definitions"]

    rows = (
        scope_activity_query(
            db.query(
                ActivitySkill.activity_id,
                ActivitySkill.skill_key,
                ActivitySkill.level,
            ).join(Activity, Activity.id == ActivitySkill.activity_id),
            admin,
            include_unowned=False,
        )
        .filter(
            counted_activity_filter(),
            ActivitySkill.target_role == target_role,
            func.extract("year", Activity.start_at) == selected_year,
            func.extract("month", Activity.start_at).in_(selected_months),
        )
        .all()
    )

    activities: dict[int, dict] = {}
    for activity_id, skill_key, level in rows:
        activities.setdefault(activity_id, {"skills": {}})["skills"][skill_key] = level

    levels_by_skill = skill_levels_from_activities(activities.values(), definitions)
    averages = average_skill_levels(levels_by_skill, ndigits=None)

    skills = []
    for skill_key in definitions:
        average = averages[skill_key]
        skills.append(
            {
                "key": skill_key,
                "averageLevel": None if average is None else round_half_up(average, 2),
                "percentage": 0 if average is None else round_half_up(average / 5 * 100),
                "evidenceCount": len(levels_by_skill[skill_key]),
            }
        )

    percentages = [item["percentage"] for item in skills if item["evidenceCount"] > 0]

    return {
        "year": selected_year,
        "months": selected_months,
        "track": track,
        "skills": skills,
        "averagePercentage": (
            round_half_up(sum(percentages) / len(percentages)) if percentages else 0
        ),
    }


@app.get("/api/admin/dashboard/external-activities")
def get_dashboard_external_activities(
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    """
    กิจกรรมภายนอกที่อนุมัติแล้วทั้งหมด (ไม่แบ่งหน้า) ให้หน้า Dashboard
    เอาไปรวมกับ /api/activities ตอนคำนวณ "การเติบโตของกิจกรรม" และ
    "Skill Distribution" ตามเดือนที่เลือกเอง (ใช้ start_date เหมือน
    start_at ของกิจกรรมปกติ, participant_skills/staff_skills รูปแบบ
    เดียวกับ /api/activities/{id} เพื่อให้ frontend ใช้ logic เดิมได้เลย)
    """

    activities = scope_student_query(
        db.query(ExternalActivity.id, ExternalActivity.start_date)
        .join(Student, Student.student_id == ExternalActivity.student_id)
        .filter(counted_external_activity_filter()),
        admin,
    ).all()

    skill_rows = scope_student_query(
        db.query(
            ExternalActivitySkill.external_activity_id,
            ExternalActivitySkill.target_role,
            ExternalActivitySkill.skill_key,
            ExternalActivitySkill.level,
        )
        .join(
            ExternalActivity,
            ExternalActivity.id == ExternalActivitySkill.external_activity_id,
        )
        .join(Student, Student.student_id == ExternalActivity.student_id)
        .filter(counted_external_activity_filter()),
        admin,
    ).all()

    skills_by_activity: dict[int, dict[str, dict]] = {}

    for activity_id, target_role, skill_key, level in skill_rows:
        bucket = skills_by_activity.setdefault(
            activity_id,
            {"participant": {}, "staff": {}},
        )
        bucket[target_role][skill_key] = level

    return {
        "external_activities": [
            {
                "id": f"external-{activity_id}",
                "start_at": start_date.isoformat(),
                "participant_skills": skills_by_activity.get(
                    activity_id, {}
                ).get("participant", {}),
                "staff_skills": skills_by_activity.get(
                    activity_id, {}
                ).get("staff", {}),
            }
            for activity_id, start_date in activities
        ],
    }


# ============================================================
# ADMIN STUDENT SKILLS
# ============================================================


def student_skill_semester_number(value) -> int:
    """Temporary semester rule: Semester 1 = Jan-Jun, Semester 2 = Jul-Dec."""
    return 1 if value.month <= 6 else 2


def student_skill_period_label(year: int, semester: str) -> str:
    if semester == "SEMESTER_1":
        return f"Semester 1/{year}"
    if semester == "SEMESTER_2":
        return f"Semester 2/{year}"
    return f"Year {year}"


def normalize_student_skill_semester(semester: str) -> str:
    normalized = (semester or "ALL").strip().upper()
    aliases = {
        "ALL": "ALL",
        "YEAR": "ALL",
        "SEMESTER_1": "SEMESTER_1",
        "SEMESTER 1": "SEMESTER_1",
        "1": "SEMESTER_1",
        "SEMESTER_2": "SEMESTER_2",
        "SEMESTER 2": "SEMESTER_2",
        "2": "SEMESTER_2",
    }
    if normalized not in aliases:
        raise HTTPException(status_code=400, detail="semester ต้องเป็น ALL, SEMESTER_1 หรือ SEMESTER_2")
    return aliases[normalized]


def student_entry_year_be(student_id: str) -> int | None:
    """
    ปีที่เข้าศึกษา (พ.ศ.) จากรหัสนักศึกษา 2 หลักแรก เช่น 67xxxxxxx = 2567
    คืน None ถ้ารหัสไม่ได้ขึ้นต้นด้วยตัวเลข 2 หลัก
    """
    prefix = str(student_id or "").strip()[:2]

    # isascii กันตัวเลขแบบอื่น (เช่น ²) ที่ isdigit ผ่านแต่ int() แปลงไม่ได้
    if len(prefix) != 2 or not (prefix.isascii() and prefix.isdigit()):
        return None

    return 2500 + int(prefix)


def report_academic_year_be(
    report_year: int,
    semester: str,
    today: date,
) -> int:
    """
    ปีการศึกษา (พ.ศ.) ที่ใช้คิดชั้นปีในรายงาน เดือนเริ่มปีการศึกษาอยู่ใน academic_calendar.py
    (ค่าเริ่มต้น ก.ค. ตรงกับ Semester 2 = ก.ค.-ธ.ค. ของหน้า Student Skills)
    - SEMESTER_1 (ม.ค.-มิ.ย.) = ปีการศึกษาที่เริ่มในปีก่อนหน้า
    - SEMESTER_2 (ก.ค.-ธ.ค.) = ปีการศึกษาที่เริ่มในปีนั้น
    - ALL = ชั้นปีล่าสุดของปีนั้น (ถ้าเป็นปีปัจจุบันและยังไม่ถึงเดือนเริ่มปีการศึกษา = ชั้นปีปัจจุบัน)
    """
    if semester == "SEMESTER_1":
        return report_year + 542

    if semester == "SEMESTER_2":
        return report_year + 543

    if (
        report_year == today.year
        and today.month < academic_calendar.ACADEMIC_YEAR_START_MONTH
    ):
        return report_year + 542

    return report_year + 543


def student_year_level(entry_year_be: int | None, academic_year_be: int) -> int | None:
    """
    ชั้นปีของนักศึกษาในปีการศึกษานั้น เช่น เข้าปี 2567 ปีการศึกษา 2569 = ชั้นปี 3
    คืน None ถ้าไม่ทราบปีที่เข้า หรือยังไม่ได้เข้าเรียนในปีการศึกษานั้น
    """
    if entry_year_be is None:
        return None

    level = academic_year_be - entry_year_be + 1

    return level if level >= 1 else None


# โหมดดู skill ในหน้า Student Skills (admin) และ My Skills (นักศึกษา)
# บทบาทในกิจกรรม -> ชุด skill ที่ได้: participant ได้ participant skills, organizer ได้ staff skills
SKILL_TRACKS = {
    "participant": {
        "member_role": "participant",
        "target_role": "participant",
        "definitions": PARTICIPANT_SKILL_DEFINITIONS,
        "label": "Participant Skills",
    },
    "staff": {
        "member_role": "organizer",
        "target_role": "staff",
        "definitions": STAFF_SKILL_DEFINITIONS,
        "label": "Staff Skills",
    },
}


def normalize_skill_track(track: str | None) -> str:
    normalized = (track or "participant").strip().lower()

    if normalized not in SKILL_TRACKS:
        raise HTTPException(
            status_code=400,
            detail="track ต้องเป็น participant หรือ staff",
        )

    return normalized


def get_student_skill_benchmarks(
    db: Session,
    track: str = "participant",
) -> dict[str, float]:
    rows = {
        row.skill_key: row.score_x100 / 100
        for row in db.query(StudentSkillBenchmark).all()
    }
    return {
        key: float(rows.get(key, 4.0))
        for key in SKILL_TRACKS[track]["definitions"]
    }


class StudentSkillBenchmarkUpdate(BaseModel):
    scores: dict[str, float]


@app.put("/api/admin/student-skills/benchmark")
def update_student_skill_benchmark(
    payload: StudentSkillBenchmarkUpdate,
    track: str = "participant",
    db: Session = Depends(get_db),
    _admin: AdminContext = Depends(require_central_admin),
):
    track = normalize_skill_track(track)
    definitions = SKILL_TRACKS[track]["definitions"]

    expected = set(definitions)
    received = set(payload.scores)
    unknown = received - expected
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown {track} skill: {', '.join(sorted(unknown))}")

    for key, raw_score in payload.scores.items():
        score = float(raw_score)
        if score < 1 or score > 5:
            raise HTTPException(status_code=400, detail=f"Benchmark {key} ต้องอยู่ระหว่าง 1.0-5.0")

        row = db.get(StudentSkillBenchmark, key)
        if row is None:
            row = StudentSkillBenchmark(skill_key=key, score_x100=round(score * 100))
            db.add(row)
        else:
            row.score_x100 = round(score * 100)

    db.commit()
    benchmarks = get_student_skill_benchmarks(db, track)
    return {
        "track": track,
        "benchmarkScores": [benchmarks[key] for key in definitions],
        "benchmarkBySkill": benchmarks,
    }


@app.get("/api/admin/student-skills")
def get_admin_student_skills(
    year: int | None = None,
    semester: str = "ALL",
    major: str | None = None,
    track: str = "participant",
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    """Student skill report for a selected year or semester.

    Calculation order is intentionally student-first:
    activity evidence -> each student's per-skill average -> faculty average.
    This prevents students with many activities from having more weight in the faculty radar.

    `major`: แอดมินกลางเลือก filter สาขาได้จากหน้า Student Skills (ดู resolve_branch_filter)
    track=participant (ค่าเริ่มต้น): skill ที่ได้จากการเป็นผู้เข้าร่วม
    track=staff: skill ที่ได้จากการเป็นผู้จัด (organizer)
    """
    admin = resolve_branch_filter(admin, major)
    selected_semester = normalize_student_skill_semester(semester)
    track = normalize_skill_track(track)
    member_role = SKILL_TRACKS[track]["member_role"]
    target_role = SKILL_TRACKS[track]["target_role"]
    definitions = SKILL_TRACKS[track]["definitions"]
    now_value = datetime.now()

    total_students = (
        scope_student_query(db.query(func.count(Student.student_id)), admin)
        .scalar()
        or 0
    )

    # Years come from both internal activities and approved external activities.
    internal_years = {
        int(value) for (value,) in db.query(func.extract("year", Activity.start_at))
        .filter(counted_activity_filter())
        .distinct().all() if value is not None
    }
    external_years = {
        int(value) for (value,) in db.query(func.extract("year", ExternalActivity.start_date))
        .filter(counted_external_activity_filter(), ExternalActivity.role == member_role)
        .distinct().all() if value is not None
    }
    available_years = sorted(internal_years | external_years | {now_value.year}, reverse=True)
    selected_year = year if year in available_years else available_years[0]

    internal_rows = scope_student_query(
        db.query(
            Student.student_id,
            Student.first_name,
            Student.last_name,
            Student.major,
            Activity.id,
            Activity.start_at,
            ActivitySkill.skill_key,
            ActivitySkill.level,
            Activity.major,
        )
        .join(ActivityMember, ActivityMember.student_id == Student.student_id)
        .join(Activity, Activity.id == ActivityMember.activity_id)
        .join(ActivitySkill, ActivitySkill.activity_id == Activity.id)
        .filter(
            ActivityMember.role == member_role,
            ActivitySkill.target_role == target_role,
            counted_activity_filter(),
            func.extract("year", Activity.start_at) == selected_year,
        ),
        admin,
    ).all()

    external_rows = scope_student_query(
        db.query(
            Student.student_id,
            Student.first_name,
            Student.last_name,
            Student.major,
            ExternalActivity.id,
            ExternalActivity.start_date,
            ExternalActivitySkill.skill_key,
            ExternalActivitySkill.level,
        )
        .join(ExternalActivity, ExternalActivity.student_id == Student.student_id)
        .join(ExternalActivitySkill, ExternalActivitySkill.external_activity_id == ExternalActivity.id)
        .filter(
            counted_external_activity_filter(),
            ExternalActivity.role == member_role,
            ExternalActivitySkill.target_role == target_role,
            func.extract("year", ExternalActivity.start_date) == selected_year,
        ),
        admin,
    ).all()

    # student_id -> accumulated evidence. activity_ids is a set, so one activity
    # counts once even when it contributes several skills.
    grouped: dict[str, dict] = {}

    def add_row(row, source: str):
        student_id, first_name, last_name, major, activity_id, start_at, skill_key, level = row[:8]
        if start_at is None or skill_key not in definitions:
            return
        sem_no = student_skill_semester_number(start_at)
        if selected_semester == "SEMESTER_1" and sem_no != 1:
            return
        if selected_semester == "SEMESTER_2" and sem_no != 2:
            return

        if student_id not in grouped:
            grouped[student_id] = {
                "id": student_id,
                "name": f"{first_name} {last_name}".strip(),
                "major": major or "",
                "skill_values": {key: [] for key in definitions},
                # แยกตามขอบเขตกิจกรรม ให้หน้ารายละเอียดนักศึกษาสลับกราฟ สาขา / คณะ
                # (ไม่นับกิจกรรมภายนอกและกิจกรรมของสาขาอื่น)
                "major_values": {key: [] for key in definitions},
                "faculty_values": {key: [] for key in definitions},
                "skill_activity_ids": {key: set() for key in definitions},
                "activity_ids": set(),
            }
        evidence_id = f"{source}:{activity_id}"
        entry = grouped[student_id]
        entry["activity_ids"].add(evidence_id)
        entry["skill_activity_ids"][skill_key].add(evidence_id)
        entry["skill_values"][skill_key].append(float(level))

        if source == "internal":
            scope = activity_source(row[8], major)
            if scope == "faculty":
                entry["faculty_values"][skill_key].append(float(level))
            elif scope == "major":
                entry["major_values"][skill_key].append(float(level))

    for row in internal_rows:
        add_row(row, "internal")
    for row in external_rows:
        add_row(row, "external")

    period_label = student_skill_period_label(selected_year, selected_semester)
    academic_year = report_academic_year_be(
        selected_year,
        selected_semester,
        now_value.date(),
    )
    students = []
    for entry in grouped.values():
        skills = average_skill_levels(entry["skill_values"])
        skill_activity_counts = {
            skill_key: len(entry["skill_activity_ids"][skill_key])
            for skill_key in definitions
        }

        students.append({
            "id": entry["id"],
            "name": entry["name"],
            "major": entry["major"],
            "yearLevel": student_year_level(
                student_entry_year_be(entry["id"]),
                academic_year,
            ),
            "semester": period_label,  # kept for existing frontend compatibility
            "periodLabel": period_label,
            "year": selected_year,
            "period": selected_semester,
            "activityCount": len(entry["activity_ids"]),
            "skillActivityCounts": skill_activity_counts,
            "skills": skills,
            "majorSkills": average_skill_levels(entry["major_values"]),
            "facultySkills": average_skill_levels(entry["faculty_values"]),
        })

    students.sort(key=lambda item: item["id"])
    benchmarks = get_student_skill_benchmarks(db, track)

    # ค่าเฉลี่ยกิจกรรมคณะของนักศึกษาทั้งคณะ (ไม่ขึ้นกับ scope สาขาของแอดมิน)
    # ให้ตรงกับกราฟ "กิจกรรมคณะ" ในหน้า My Skills ของนักศึกษา
    faculty_activity_average = scoped_skill_average_for_period(
        db,
        selected_year,
        {"SEMESTER_1": 1, "SEMESTER_2": 2}.get(selected_semester),
        track,
        None,
    )

    # จำนวนนักศึกษาทั้งหมดแยกตามชั้นปี (ในปีการศึกษาที่ใช้) และสาขา
    # ให้หน้าเว็บคำนวณ "% ของนักศึกษา" ได้ถูกต้องเมื่อกรองตามชั้นปี/สาขา
    # นับเฉพาะนักศึกษาที่แอดมินคนนี้เห็น (แอดมินสาขาเห็นแค่สาขาตัวเอง)
    population_counts: dict[tuple[int | None, str], int] = {}

    population_rows = scope_student_query(
        db.query(Student.student_id, Student.major),
        admin,
    ).all()

    for student_id, major in population_rows:
        entry_year = student_entry_year_be(student_id)
        level = student_year_level(entry_year, academic_year)

        # ยังไม่ได้เข้าเรียนในปีนั้นจึงไม่นับ ยกเว้นคนที่มีข้อมูล skill ในรายงานนี้
        # (เช่นกิจกรรมภายนอกก่อนเข้าเรียน) ให้นับตรงกับรายชื่อด้านบนที่แสดงเป็น "ไม่ทราบชั้นปี"
        if entry_year is not None and level is None and student_id not in grouped:
            continue

        key = (level, major or "")
        population_counts[key] = population_counts.get(key, 0) + 1

    population = [
        {"yearLevel": level, "major": major, "count": count}
        for (level, major), count in population_counts.items()
    ]

    return {
        "years": available_years,
        "availableYears": available_years,
        "defaultYear": selected_year,
        "selectedYear": selected_year,
        "selectedSemester": selected_semester,
        "periodLabel": period_label,
        "periodOptions": ["ALL", "SEMESTER_1", "SEMESTER_2"],
        "totalFaculty": total_students,
        "totalFacultyBySemester": {period_label: total_students},
        "population": population,
        "track": track,
        "benchmarkScores": [benchmarks[key] for key in definitions],
        "benchmarkBySkill": benchmarks,
        "facultyActivityAverage": faculty_activity_average,
        "skillDefinitions": [
            {"key": key, "label": label}
            for key, label in definitions.items()
        ],
        "students": students,
    }


@app.get("/api/admin/students/{student_id}/activities")
def get_admin_student_activities(
    student_id: str,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    """
    ประวัติกิจกรรมทั้งหมดของนักศึกษา 1 คน (มุมมอง Admin) ใช้กับปุ่ม
    "ดูกิจกรรม" ในหน้า Student Skills

    ต่างจาก /api/student/me/activities ตรงที่กิจกรรมภายนอกจะคืนมา
    "ทุกสถานะ" (pending/approved/rejected) เพราะ admin ต้องเห็น
    ประวัติทั้งหมด ไม่ใช่แค่ที่อนุมัติแล้ว
    """
    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบนักศึกษา",
        )

    ensure_can_access_student(admin, student)

    items = []

    # กิจกรรมของคณะที่นักศึกษาคนนี้เข้าร่วมอาจเป็นของสาขาอื่นก็ได้ จึงต้อง
    # กรองด้วย scope_activity_query ซ้ำอีกชั้น ไม่ใช่แค่กรองตัวนักศึกษา
    memberships = scope_activity_query(
        db.query(ActivityMember, Activity).join(
            Activity, Activity.id == ActivityMember.activity_id
        ),
        admin,
    ).filter(ActivityMember.student_id == student_id).all()

    for member, activity in memberships:
        items.append(
            {
                "source": "activity",
                "id": activity.id,
                "title": activity.name,
                "activity_type": activity.activity_type,
                "start_at": activity.start_at,
                "end_at": activity.end_at,
                "role": member.role,
                # กิจกรรมของคณะ: admin เป็นคนเพิ่มสมาชิกเอง ถือว่า
                # approved แล้วโดยปริยาย ไม่มี workflow อนุมัติแยก
                "status": "approved",
            }
        )

    external_activities = (
        db.query(ExternalActivity)
        .filter(ExternalActivity.student_id == student_id)
        .all()
    )

    for external_activity in external_activities:
        items.append(
            {
                "source": "external_activity",
                "id": external_activity.id,
                "title": external_activity.title,
                "activity_type": external_activity.activity_type,
                "start_at": datetime.combine(
                    external_activity.start_date,
                    datetime.min.time(),
                ),
                "end_at": datetime.combine(
                    external_activity.end_date,
                    datetime.min.time(),
                ),
                "role": external_activity.role,
                "status": external_activity.status,
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
        },
        "total": len(items),
        "activities": items,
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
    admin: AdminContext,
) -> tuple[int, int]:
    # นับผ่าน Student เพื่อกรองตามสาขาแอดมินเหมือนกับ get_activity_participants
    # ไม่งั้นจำนวนที่โชว์ในหน้า list จะไม่ตรงกับรายชื่อจริงที่เห็นในหน้า detail
    participant_count = (
        scope_student_query(
            db.query(func.count(ActivityMember.student_id))
            .join(
                Student,
                Student.student_id == ActivityMember.student_id,
            )
            .filter(
                ActivityMember.activity_id == activity_id,
                ActivityMember.role == "participant",
            ),
            admin,
        )
        .scalar()
        or 0
    )

    organizer_count = (
        scope_student_query(
            db.query(func.count(ActivityMember.student_id))
            .join(
                Student,
                Student.student_id == ActivityMember.student_id,
            )
            .filter(
                ActivityMember.activity_id == activity_id,
                ActivityMember.role == "organizer",
            ),
            admin,
        )
        .scalar()
        or 0
    )

    return participant_count, organizer_count


def get_member_counts_by_activity(
    db: Session,
    admin: AdminContext,
) -> dict[int, tuple[int, int]]:
    # นับสมาชิกทุกกิจกรรมใน query เดียว แทนการนับทีละกิจกรรม
    # กรองตามสาขาแอดมินเหมือนกับ get_activity_participants ด้วยเหตุผลเดียวกัน
    counts: dict[int, list[int]] = {}

    query = scope_student_query(
        db.query(
            ActivityMember.activity_id,
            ActivityMember.role,
            func.count(ActivityMember.student_id),
        ).join(
            Student,
            Student.student_id == ActivityMember.student_id,
        ),
        admin,
    ).group_by(ActivityMember.activity_id, ActivityMember.role)

    for activity_id, role, total in query.all():
        entry = counts.setdefault(activity_id, [0, 0])
        if role == "participant":
            entry[0] = total
        elif role == "organizer":
            entry[1] = total

    return {activity_id: (entry[0], entry[1]) for activity_id, entry in counts.items()}


def serialize_activity(
    db: Session,
    activity: Activity,
    admin: AdminContext,
    include_skills: bool = False,
    member_counts: tuple[int, int] | None = None,
) -> dict:
    participant_count, organizer_count = (
        member_counts
        if member_counts is not None
        else get_member_counts(db, activity.id, admin)
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
    admin: AdminContext,
) -> Activity:
    activity = db.get(Activity, activity_id)

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบกิจกรรม",
        )

    ensure_can_access_activity(admin, activity)

    return activity


@app.get("/api/activities")
def list_activities(
    owned_only: bool = False,
    major: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    # โหลด skill ของทุกกิจกรรมและจำนวนสมาชิกรวดเดียว ไม่ query ซ้ำทีละกิจกรรม
    # แอดมินสาขาเห็นเฉพาะกิจกรรมของสาขาตัวเอง + กิจกรรมที่ยังไม่มีเจ้าของ (major=None)
    # ตามค่าเริ่มต้น -- หน้า Dashboard ที่คำนวณ Activity Growth/Skill Distribution
    # เองฝั่ง frontend ส่ง owned_only=true มา เพื่อไม่นับกิจกรรมที่ยังไม่มีเจ้าของ
    # เป็นสถิติของสาขาไหนสาขาหนึ่ง
    # major: แอดมินกลางเลือก filter สาขาได้จากหน้า Activities (ดู resolve_branch_filter)
    admin = resolve_branch_filter(admin, major)
    activities = (
        scope_activity_query(db.query(Activity), admin, include_unowned=not owned_only)
        .options(selectinload(Activity.skill_levels))
        .order_by(Activity.start_at.asc())
        .all()
    )
    member_counts = get_member_counts_by_activity(db, admin)

    return {
        "total": len(activities),
        "activities": [
            serialize_activity(
                db,
                activity,
                admin,
                include_skills=True,
                member_counts=member_counts.get(activity.id, (0, 0)),
            )
            for activity in activities
        ],
    }


@app.post("/api/activities", status_code=201)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
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
        # แอดมินสาขาสร้างกิจกรรมเป็นของสาขาตัวเองอัตโนมัติ ส่วนแอดมินกลาง
        # สร้างแล้วเห็นได้ทุกแอดมิน (major=None)
        major=None if admin.is_central else admin.major,
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
        admin,
        include_skills=True,
    )




@app.patch("/api/activities/{activity_id}")
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    activity = require_activity(
        db,
        activity_id,
        admin,
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
        admin,
        include_skills=True,
    )


@app.get("/api/activities/{activity_id}")
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    activity = require_activity(
        db,
        activity_id,
        admin,
    )

    return serialize_activity(
        db,
        activity,
        admin,
        include_skills=True,
    )


@app.delete(
    "/api/activities/{activity_id}",
    status_code=204,
)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    activity = require_activity(
        db,
        activity_id,
        admin,
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
    *,
    require_email: bool = True,
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

        email = row["email"]

        # ไฟล์เช็คชื่อรุ่นเก่า (.xls) ไม่มี column email เลย
        # จึงไม่บังคับว่าต้องมี แต่ถ้ามีค่ามาก็ยังตรวจรูปแบบ
        if require_email and not email:
            errors.append("ไม่มีอีเมล")
        elif email and "@" not in email:
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


def read_student_file(
    file: UploadFile,
) -> dict:
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in {
        ".csv",
        ".xlsx",
        ".xls",
    }:
        raise HTTPException(
            status_code=400,
            detail="รองรับเฉพาะไฟล์ .csv, .xlsx และ .xls",
        )

    contents = read_import_upload(file)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์ว่าง",
        )

    ensure_import_file_within_limits(contents, extension)

    is_legacy_xls = extension == ".xls"

    if is_legacy_xls:
        # ไฟล์ export จากระบบเช็คชื่อรุ่นเก่า: จำนวนแถว metadata
        # ก่อน header ไม่คงที่ (บางไฟล์มีแถวว่างแทรก) จึงหา
        # แถว header จริงจากเนื้อหาแทนการนับจำนวนแถวตายตัว
        df = read_legacy_xls_dataframe(contents)
    else:
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

    if is_legacy_xls:
        # ไฟล์นี้ไม่มี column email และมีแค่ชื่อเต็ม (ไม่แยก
        # ชื่อ/นามสกุล) จึงต้องตัดชื่อเต็มเองและปล่อย email ว่าง
        df = normalize_legacy_student_columns(df)

        first_names = []
        last_names = []

        for full_name in df["full_name"]:
            first_name, last_name = split_full_name(
                str(full_name).strip()
            )
            first_names.append(first_name)
            last_names.append(last_name)

        df["first_name"] = first_names
        df["last_name"] = last_names
        df["email"] = ""
        df["major"] = ""
        df["role"] = "participant"

        df = df[
            [
                "student_id",
                "first_name",
                "last_name",
                "email",
                "faculty",
                "major",
                "role",
            ]
        ]

        invalid_rows = validate_students(
            df,
            require_email=False,
        )
    else:
        df = normalize_student_columns(df)
        invalid_rows = validate_students(df)

    # แสดงชื่อคณะหลังแปลงแล้ว (เหมือนตอนบันทึก) แต่ค่าว่างคงไว้
    # เพราะตอน confirm ค่าว่าง = คงคณะเดิมของนักศึกษาที่มีอยู่แล้ว
    df["faculty"] = [
        normalize_faculty(value) if str(value).strip() else ""
        for value in df["faculty"]
    ]

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
# STUDENTS
# ============================================================


def import_students_from_xlsx(
    filename: str,
    contents: bytes,
    db: Session,
) -> dict:
    """
    ไฟล์ master data ทั่วไป: student_id, first_name, last_name,
    email, faculty, major
    """
    try:
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

    id_column = df["student_id"].astype(str).str.strip()
    duplicate_ids_in_file = set(
        id_column[
            id_column.ne("") & id_column.duplicated(keep=False)
        ]
    )

    failed_rows = []
    new_students: dict[str, Student] = {}

    for index, row in df.iterrows():
        row_number = int(index) + 2

        student_id = str(row.get("student_id", "")).strip()
        first_name = str(row.get("first_name", "")).strip()
        last_name = str(row.get("last_name", "")).strip()
        email = str(row.get("email", "")).strip()
        faculty = normalize_faculty(row.get("faculty"))
        major = str(row.get("major", "")).strip()

        errors = []

        if not student_id:
            errors.append("ไม่มีรหัสนักศึกษา")

        if not first_name:
            errors.append("ไม่มีชื่อ")

        if not last_name:
            errors.append("ไม่มีนามสกุล")

        if not email:
            errors.append("ไม่มีอีเมล")
        elif "@" not in email:
            errors.append("รูปแบบอีเมลไม่ถูกต้อง")

        if student_id and student_id in duplicate_ids_in_file:
            errors.append("รหัสนักศึกษาซ้ำในไฟล์")
        elif student_id and db.get(Student, student_id) is not None:
            errors.append("มีรหัสนักศึกษานี้ในระบบแล้ว")

        if errors:
            failed_rows.append(
                {
                    "row": row_number,
                    "student_id": student_id,
                    "errors": errors,
                }
            )
            continue

        new_students[student_id] = Student(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            faculty=faculty,
            major=major,
        )

    for student in new_students.values():
        db.add(student)

    db.commit()

    return {
        "filename": filename,
        "total": len(df),
        "success_count": len(new_students),
        "failed_count": len(failed_rows),
        "failed_rows": failed_rows,
    }


LEGACY_STUDENT_COLUMN_ALIASES = {
    "ลำดับ": "seq",
    "รหัสนักศึกษา": "student_id",
    "ชื่อ": "full_name",
    "คณะ": "faculty",
    "เวลา": "check_in_time",
}

LEGACY_STUDENT_REQUIRED_COLUMNS = [
    "student_id",
    "full_name",
    "faculty",
]


LEGACY_HEADER_MARKER_ALIASES = {
    "รหัสนักศึกษา",
    "ชื่อ",
}


def find_legacy_header_row(raw_df: pd.DataFrame) -> int:
    for index, row in raw_df.iterrows():
        cells = {
            normalize_text(value)
            for value in row.tolist()
            if pd.notna(value)
        }

        if LEGACY_HEADER_MARKER_ALIASES.issubset(cells):
            return int(index)

    raise HTTPException(
        status_code=400,
        detail=(
            "ไม่พบแถว header ที่มีคอลัมน์ "
            "รหัสนักศึกษา, ชื่อ ในไฟล์"
        ),
    )


def read_legacy_xls_dataframe(
    contents: bytes,
) -> pd.DataFrame:
    """
    ไฟล์ export จากระบบเช็คชื่อรุ่นเก่ามีแถว metadata นำหน้า
    header จริง แต่จำนวนแถวไม่คงที่ระหว่างไฟล์ (บางไฟล์มีแถวว่าง
    แทรกอยู่) จึงหาแถว header จากเนื้อหาจริงแทนการ skiprows
    แบบตายตัว
    """
    try:
        raw = pd.read_excel(
            BytesIO(contents),
            engine="xlrd",
            header=None,
            dtype=str,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"ไม่สามารถอ่านไฟล์ได้: {exc}",
        )

    header_row = find_legacy_header_row(raw)

    df = raw.iloc[header_row + 1 :].copy()
    df.columns = [
        normalize_text(value) if pd.notna(value) else ""
        for value in raw.iloc[header_row].tolist()
    ]

    return df.reset_index(drop=True)


def normalize_legacy_student_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df.columns = [
        normalize_text(column) for column in df.columns
    ]

    rename_map = {
        column: LEGACY_STUDENT_COLUMN_ALIASES[
            normalize_text(column)
        ]
        for column in df.columns
        if normalize_text(column)
        in LEGACY_STUDENT_COLUMN_ALIASES
    }

    df = df.rename(columns=rename_map)

    missing_columns = [
        column
        for column in LEGACY_STUDENT_REQUIRED_COLUMNS
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

    df = df[LEGACY_STUDENT_REQUIRED_COLUMNS].copy()
    df = df.fillna("")

    for column in LEGACY_STUDENT_REQUIRED_COLUMNS:
        df[column] = df[column].astype(str).str.strip()

    return df


def split_full_name(full_name: str) -> tuple[str, str]:
    # ชื่อไทยไม่มี column แยกนามสกุล จึงตัดคำแรกเป็นชื่อ
    # ที่เหลือ (ถ้ามี) เป็นนามสกุล
    parts = full_name.split(None, 1)

    if not parts:
        return "", ""

    if len(parts) == 1:
        return parts[0], ""

    return parts[0], parts[1]


def import_students_from_legacy_xls(
    filename: str,
    contents: bytes,
    db: Session,
) -> dict:
    """
    ไฟล์ export จากระบบเช็คชื่อรุ่นเก่า (.xls / BIFF): มีแถว
    metadata นำหน้า (รหัสกิจกรรม, ชื่อกิจกรรม, เวลา export, จำนวน
    ฯลฯ) จำนวนไม่คงที่ระหว่างไฟล์ ตามด้วย header จริง: ลำดับ,
    รหัสนักศึกษา, ชื่อ, คณะ, เวลา แล้วเป็นข้อมูลนักศึกษา

    ไฟล์นี้ไม่มี email และมีแค่ชื่อเต็ม (ไม่แยกชื่อ/นามสกุล) จึง
    ต้องตัดชื่อเต็มเอง และเก็บ email เป็นค่าว่าง เพราะไม่มีข้อมูลจริง
    """
    df = read_legacy_xls_dataframe(contents)
    df = normalize_legacy_student_columns(df)

    id_column = df["student_id"].astype(str).str.strip()
    duplicate_ids_in_file = set(
        id_column[
            id_column.ne("") & id_column.duplicated(keep=False)
        ]
    )

    errors = []
    warnings = []
    seen_ids: set[str] = set()
    new_students: dict[str, Student] = {}

    for index, row in df.iterrows():
        # นับ row แบบสัมพัทธ์กับตารางที่ตัด header ออกแล้ว
        # (เหมือน read_student_file) ไม่ใช่เลขแถวจริงในไฟล์ .xls
        row_number = int(index) + 2

        student_id = str(row.get("student_id", "")).strip()
        full_name = str(row.get("full_name", "")).strip()
        faculty = str(row.get("faculty", "")).strip()

        if not student_id:
            errors.append(
                {
                    "row": row_number,
                    "reason": "ไม่มีรหัสนักศึกษา",
                }
            )
            continue

        if (
            student_id in duplicate_ids_in_file
            and student_id in seen_ids
        ):
            warnings.append(
                {
                    "row": row_number,
                    "student_id": student_id,
                    "reason": "รหัสนักศึกษาซ้ำในไฟล์ ข้ามแถวนี้",
                }
            )
            continue

        if db.get(Student, student_id) is not None:
            seen_ids.add(student_id)
            warnings.append(
                {
                    "row": row_number,
                    "student_id": student_id,
                    "reason": "มีรหัสนักศึกษานี้ในระบบแล้ว ข้ามแถวนี้",
                }
            )
            continue

        seen_ids.add(student_id)

        first_name, last_name = split_full_name(full_name)

        new_students[student_id] = Student(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            email="",
            faculty=normalize_faculty(faculty),
            major="",
        )

    for student in new_students.values():
        db.add(student)

    db.commit()

    return {
        "filename": filename,
        "total": len(df),
        "success": len(new_students),
        "skipped": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


@app.post("/api/students/import", status_code=201)
def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: AdminContext = Depends(require_central_admin),
):
    """
    นำเข้านักศึกษาแบบ bulk โดยไม่ผูกกับกิจกรรมใดๆ (ต่างจาก
    /api/activities/{id}/participants/import ที่แนบนักศึกษาเข้า
    กิจกรรมไปด้วย)

    - .xlsx : ไฟล์ master data ทั่วไป (student_id, first_name,
      last_name, email, faculty, major)
    - .xls  : ไฟล์ export จากระบบเช็คชื่อรุ่นเก่า (ดู
      import_students_from_legacy_xls)
    """
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in {".xlsx", ".xls"}:
        raise HTTPException(
            status_code=400,
            detail="รองรับเฉพาะไฟล์ .xlsx และ .xls เท่านั้น",
        )

    contents = read_import_upload(file)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์ว่าง",
        )

    ensure_import_file_within_limits(contents, extension)

    if extension == ".xls":
        return import_students_from_legacy_xls(
            filename,
            contents,
            db,
        )

    return import_students_from_xlsx(
        filename,
        contents,
        db,
    )


# ============================================================
# ADMIN SETTINGS: IMPORT STUDENTS (central admin)
# ============================================================

# หัวคอลัมน์ของไฟล์ template (ชื่อเดียวกับ COLUMN_ALIASES ด้านบน)
STUDENT_IMPORT_TEMPLATE_HEADERS = [
    ("รหัสนักศึกษา", "student_id"),
    ("ชื่อ", "first_name"),
    ("นามสกุล", "last_name"),
    ("อีเมล", "email"),
    ("สาขาวิชา", "major"),
]
STUDENT_IMPORT_MAX_ROWS = 5000
STUDENT_IMPORT_FIELD_LIMITS = {
    "student_id": 30,
    "first_name": 150,
    "last_name": 150,
    "email": 255,
    "major": 255,
}


def clean_import_cell(value) -> str:
    text = normalize_text(value if value is not None else "")
    # Excel เก็บรหัสเป็นตัวเลขแล้วอ่านออกมาเป็น "670510301.0"
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


STUDENT_IMPORT_EXTENSIONS = {".xlsx", ".xls", ".csv"}
# CSV ภาษาไทยจาก Excel: UTF-8 (มัก BOM) หรือ Windows-874 (TIS-620) ตามเครื่องที่บันทึก
STUDENT_IMPORT_CSV_ENCODINGS = ("utf-8-sig", "cp874")


def read_student_import_csv(contents: bytes) -> pd.DataFrame:
    for encoding in STUDENT_IMPORT_CSV_ENCODINGS:
        try:
            text = contents.decode(encoding)
        except UnicodeDecodeError:
            continue

        # sep=None: เดาตัวคั่นเอง (Excel บางภาษาบันทึกเป็น ; แทน ,)
        return pd.read_csv(
            StringIO(text),
            sep=None,
            engine="python",
            dtype=str,
            keep_default_na=False,
            skip_blank_lines=True,
        )

    raise ValueError("unsupported encoding")


def build_student_import_rows(contents: bytes, extension: str, db: Session) -> list[dict]:
    try:
        # keep_default_na=False: ช่องว่างเป็น "" ไม่ใช่ "nan"
        if extension == ".csv":
            df = read_student_import_csv(contents)
        else:
            df = pd.read_excel(BytesIO(contents), dtype=str, keep_default_na=False)
    except Exception:
        raise HTTPException(status_code=400, detail="ไม่สามารถอ่านไฟล์ได้ กรุณาใช้ไฟล์ .xlsx, .xls หรือ .csv")

    aliases = {normalize_text(key): value for key, value in COLUMN_ALIASES.items()}
    df = df.rename(columns={column: aliases.get(normalize_text(column), column) for column in df.columns})

    if "student_id" not in df.columns:
        expected = ", ".join(label for label, _ in STUDENT_IMPORT_TEMPLATE_HEADERS)
        raise HTTPException(status_code=400, detail=f"ไม่พบคอลัมน์ รหัสนักศึกษา (คอลัมน์ที่ต้องมี: {expected})")

    if len(df) > STUDENT_IMPORT_MAX_ROWS:
        raise HTTPException(status_code=400, detail=f"นำเข้าได้ครั้งละไม่เกิน {STUDENT_IMPORT_MAX_ROWS} แถว")

    records = []
    for index, raw in enumerate(df.to_dict("records")):
        record = {field: clean_import_cell(raw.get(field, "")) for _, field in STUDENT_IMPORT_TEMPLATE_HEADERS}
        # ข้ามแถวว่างทั้งแถว (มักเป็นแถวท้ายไฟล์)
        if any(record.values()):
            records.append({"row": index + 2, **record})

    ids = {record["student_id"] for record in records if record["student_id"]}
    existing = {
        student_id
        for (student_id,) in db.query(Student.student_id).filter(Student.student_id.in_(ids)).all()
    } if ids else set()

    seen = set()
    for record in records:
        problems = []
        if not record["student_id"]:
            problems.append("ไม่มีรหัสนักศึกษา")
        if not record["first_name"]:
            problems.append("ไม่มีชื่อ")
        if not record["last_name"]:
            problems.append("ไม่มีนามสกุล")
        if record["email"] and "@" not in record["email"]:
            problems.append("รูปแบบอีเมลไม่ถูกต้อง")
        for field, limit in STUDENT_IMPORT_FIELD_LIMITS.items():
            if len(record[field]) > limit:
                problems.append(f"{field} ยาวเกิน {limit} ตัวอักษร")

        if problems:
            record["status"], record["message"] = "invalid", ", ".join(problems)
        elif record["student_id"] in existing:
            record["status"], record["message"] = "duplicate", "มีรหัสนักศึกษานี้ในระบบแล้ว"
        elif record["student_id"] in seen:
            record["status"], record["message"] = "duplicate", "รหัสนักศึกษาซ้ำในไฟล์"
        else:
            record["status"], record["message"] = "new", ""
            seen.add(record["student_id"])

    return records


@app.get("/api/admin/students/import/template")
def download_student_import_template(_admin: AdminContext = Depends(require_central_admin)):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "students"
    sheet.append([label for label, _ in STUDENT_IMPORT_TEMPLATE_HEADERS])

    for cell in sheet[1]:
        cell.font = openpyxl.styles.Font(bold=True)
    for letter, width in zip("ABCDE", (18, 22, 22, 32, 30)):
        sheet.column_dimensions[letter].width = width
        # คอลัมน์เป็นข้อความ: รหัสนักศึกษาไม่ถูกแปลงเป็นตัวเลข
        for row in range(2, 1001):
            sheet[f"{letter}{row}"].number_format = "@"
    sheet.freeze_panes = "A2"

    buffer = BytesIO()
    workbook.save(buffer)

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="student-import-template.xlsx"'},
    )


@app.post("/api/admin/students/import")
def import_students_from_settings(
    file: UploadFile = File(...),
    dry_run: bool = False,
    db: Session = Depends(get_db),
    _admin: AdminContext = Depends(require_central_admin),
):
    """
    นำเข้านักศึกษาจากหน้า Settings: dry_run=true = พรีวิวอย่างเดียว ไม่บันทึก
    รหัสที่มีอยู่แล้ว (หรือซ้ำในไฟล์) ข้ามโดยไม่ error, แถวไม่ถูกต้องนับเป็น failed
    """
    extension = Path(file.filename or "").suffix.lower()

    if extension not in STUDENT_IMPORT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ .xlsx, .xls และ .csv เท่านั้น")

    contents = read_import_upload(file)
    if not contents:
        raise HTTPException(status_code=400, detail="ไฟล์ว่าง")
    ensure_import_file_within_limits(contents, extension)

    rows = build_student_import_rows(contents, extension, db)

    if not dry_run:
        for record in rows:
            if record["status"] == "new":
                db.add(
                    Student(
                        student_id=record["student_id"],
                        first_name=record["first_name"],
                        last_name=record["last_name"],
                        email=record["email"],
                        faculty="Faculty of Science",
                        major=record["major"],
                    )
                )
        db.commit()

    count = lambda status: sum(1 for record in rows if record["status"] == status)  # noqa: E731

    return {
        "dry_run": dry_run,
        "total": len(rows),
        "success": count("new"),
        "skipped": count("duplicate"),
        "failed": count("invalid"),
        "errors": [
            {
                "row": record["row"],
                "student_id": record["student_id"],
                "type": record["status"],
                "message": record["message"],
            }
            for record in rows
            if record["status"] != "new"
        ],
        "rows": rows,
    }


# ============================================================
# ADMIN SETTINGS: MANAGE STUDENTS (central admin)
# ============================================================


def serialize_settings_student(student: Student, activity_count: int, external_count: int) -> dict:
    return {
        "student_id": student.student_id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "email": student.email,
        "faculty": student.faculty,
        "major": student.major,
        "created_at": student.created_at,
        "activity_count": activity_count,
        "external_activity_count": external_count,
    }


@app.get("/api/admin/students")
def list_students_for_settings(
    search: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _admin: AdminContext = Depends(require_central_admin),
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    query = db.query(Student)
    keyword = search.strip()

    if keyword:
        pattern = f"%{keyword.lower()}%"
        query = query.filter(
            or_(
                func.lower(Student.student_id).like(pattern),
                func.lower(Student.first_name).like(pattern),
                func.lower(Student.last_name).like(pattern),
                func.lower(Student.email).like(pattern),
                func.lower(Student.major).like(pattern),
            )
        )

    total = query.count()
    students = (
        query.order_by(Student.created_at.desc(), Student.student_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    ids = [student.student_id for student in students]

    def counts(model, column):
        if not ids:
            return {}
        return dict(
            db.query(column, func.count())
            .filter(column.in_(ids))
            .group_by(column)
            .all()
        )

    activity_counts = counts(ActivityMember, ActivityMember.student_id)
    external_counts = counts(ExternalActivity, ExternalActivity.student_id)

    return {
        "total": total,
        "all_total": db.query(func.count(Student.student_id)).scalar(),
        "page": page,
        "page_size": page_size,
        "students": [
            serialize_settings_student(
                student,
                activity_counts.get(student.student_id, 0),
                external_counts.get(student.student_id, 0),
            )
            for student in students
        ],
    }


def delete_students_and_related(db: Session, students: list[Student]) -> dict:
    """ลบนักศึกษา + ข้อมูลที่ผูกอยู่ทั้งหมด คืนจำนวนที่ลบแต่ละประเภท

    memberships / external activities ลบตาม ORM cascade (skills, evidence,
    notification ของ external activity ลบตาม FK CASCADE) ส่วน notification
    และคำขอทั่วไปไม่มี FK ไปที่ students จึงลบเองตาม student_id
    """
    ids = [student.student_id for student in students]
    if not ids:
        return {"students": 0, "activity_memberships": 0, "external_activities": 0, "requests": 0, "notifications": 0}

    external = db.query(ExternalActivity).filter(ExternalActivity.student_id.in_(ids)).all()
    # เก็บ path ไฟล์ไว้ก่อน (ลบหลัง commit สำเร็จเท่านั้น)
    evidence_paths = [
        path
        for activity in external
        for evidence in activity.evidence_files
        if (path := find_evidence_path(evidence)) is not None
    ]
    folders = [evidence_folder(activity.id) for activity in external]

    summary = {
        "students": len(ids),
        "activity_memberships": db.query(ActivityMember).filter(ActivityMember.student_id.in_(ids)).count(),
        "external_activities": len(external),
        "requests": db.query(StudentRequest).filter(StudentRequest.requester_student_id.in_(ids)).count(),
        "notifications": db.query(Notification).filter(Notification.student_id.in_(ids)).count(),
    }

    db.query(Notification).filter(Notification.student_id.in_(ids)).delete(synchronize_session=False)
    db.query(StudentRequest).filter(StudentRequest.requester_student_id.in_(ids)).delete(synchronize_session=False)
    for student in students:
        db.delete(student)
    db.commit()

    for path in evidence_paths:
        path.unlink(missing_ok=True)
    for folder in folders:
        shutil.rmtree(folder, ignore_errors=True)

    return summary


@app.delete("/api/admin/students/{student_id}")
def delete_student_from_settings(
    student_id: str,
    db: Session = Depends(get_db),
    _admin: AdminContext = Depends(require_central_admin),
):
    student = db.get(Student, student_id.strip())

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนักศึกษานี้ในระบบ")

    return delete_students_and_related(db, [student])


@app.delete("/api/admin/students")
def delete_all_students_from_settings(
    confirm: str = "",
    db: Session = Depends(get_db),
    _admin: AdminContext = Depends(require_central_admin),
):
    # กันกดพลาด/เรียกผิด: ต้องส่ง ?confirm=all มาเท่านั้น
    if confirm != "all":
        raise HTTPException(status_code=400, detail="ต้องยืนยันการลบทั้งหมด (confirm=all)")

    return delete_students_and_related(db, db.query(Student).all())


# ============================================================
# PARTICIPANTS
# ============================================================


def serialize_student_lookup(student: Student) -> dict:
    return {
        "student_id": student.student_id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "email": student.email,
        "faculty": student.faculty,
        "major": student.major,
    }


@app.get("/api/admin/students/lookup")
def lookup_student_by_id(
    student_id: str,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    # ใช้กับหน้า Add Participant: พิมพ์ student_id แล้วดึงชื่อ/คณะ/สาขามาเติม
    # ให้อัตโนมัติ ไม่จำกัด major เพราะกิจกรรมหนึ่งอาจมีผู้เข้าร่วมข้ามสาขาได้
    # (เหมือน behavior เดิมตอนพิมพ์ฟอร์มมือ ไม่เคยจำกัดด้วย major)
    value = student_id.strip()

    if not value:
        raise HTTPException(status_code=400, detail="กรุณาระบุรหัสนักศึกษา")

    student = db.get(Student, value)

    if not student:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบรหัสนักศึกษานี้ในระบบ",
        )

    return serialize_student_lookup(student)


@app.get("/api/admin/students/search")
def search_students(
    q: str = "",
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    # Autocomplete ค้นหาด้วยรหัสนักศึกษาหรือชื่อ-นามสกุล ใช้กับหน้า Add Participant
    keyword = q.strip()

    if not keyword:
        return {"students": []}

    limit = max(1, min(limit, 25))
    pattern = f"%{keyword}%"

    students = (
        db.query(Student)
        .filter(
            or_(
                Student.student_id.ilike(pattern),
                Student.first_name.ilike(pattern),
                Student.last_name.ilike(pattern),
                (Student.first_name + " " + Student.last_name).ilike(pattern),
            )
        )
        .order_by(Student.student_id)
        .limit(limit)
        .all()
    )

    return {"students": [serialize_student_lookup(student) for student in students]}


@app.post(
    "/api/activities/{activity_id}/participants/import/preview"
)
def preview_activity_participants(
    activity_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    require_activity(
        db,
        activity_id,
        admin,
    )

    result = read_student_file(file)

    return {
        "activity_id": activity_id,
        **result,
    }


class ConfirmImportRequest(BaseModel):
    students: list[dict] = Field(max_length=MAX_IMPORT_ROWS)


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
    admin: AdminContext = Depends(get_current_admin),
):
    require_activity(
        db,
        activity_id,
        admin,
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

        # email / faculty / major ไม่บังคับ ไฟล์บางแบบ (เช่น .xls จากระบบเช็คอินเก่า)
        # ไม่มีคอลัมน์เหล่านี้ ค่าว่างจึงแปลว่า "ไม่รู้" ไม่ใช่ "ลบค่าเดิม"
        email = str(raw_student.get("email") or "").strip()
        faculty = str(raw_student.get("faculty") or "").strip()
        major = str(raw_student.get("major") or "").strip()

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

        if email and "@" not in email:
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
            # ไฟล์ไม่มี major (เช่น .xls เช็คอินเก่า) และแอดมินที่ import เป็น
            # แอดมินสาขา (ไม่ใช่แอดมินกลาง) ให้ใช้สาขาของแอดมินคนนั้นแทน
            # ไม่งั้นนักศึกษาที่เพิ่ง import จะหลุดออกจาก scope ของแอดมินคนนำเข้าเอง
            new_student_major = major
            if not new_student_major and not admin.is_central:
                new_student_major = admin.major

            student = Student(
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                faculty=normalize_faculty(faculty),
                major=new_student_major,
            )

            db.add(student)
            db.flush()
        elif can_access_student(admin, student):
            # ถ้า import ข้อมูลล่าสุดเข้ามา ให้อัปเดต master data ด้วย
            # ช่องที่ไม่บังคับอัปเดตเฉพาะเมื่อไฟล์มีค่า ไม่งั้นคงค่าเดิมไว้
            student.first_name = first_name
            student.last_name = last_name
            if email:
                student.email = email
            if faculty:
                student.faculty = normalize_faculty(faculty)
            # แอดมินสาขาย้ายนักศึกษาไปสาขาอื่นไม่ได้ (เหมือน ensure_can_assign_major)
            if major and (admin.is_central or major == admin.major):
                student.major = major
        # นักศึกษาสาขาอื่น: เพิ่มเป็นผู้เข้าร่วมได้ แต่ไม่แก้ master data ของสาขานั้น

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
    admin: AdminContext = Depends(get_current_admin),
):
    activity = require_activity(
        db,
        activity_id,
        admin,
    )

    # กิจกรรมของคณะใช้ร่วมกันทุกแอดมิน แต่รายชื่อผู้เข้าร่วมเห็นเฉพาะสาขาตัวเอง
    rows = (
        scope_student_query(
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
            ),
            admin,
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
    admin: AdminContext = Depends(get_current_admin),
):
    require_activity(
        db,
        activity_id,
        admin,
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
    ensure_can_access_student(admin, student)

    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    email = payload.email.strip()
    faculty = normalize_faculty(payload.faculty)
    major = payload.major.strip()
    role = normalize_role(payload.role)

    ensure_can_assign_major(admin, major)

    if not first_name or not last_name:
        raise HTTPException(
            status_code=400,
            detail="ชื่อ/นามสกุลไม่ครบ",
        )

    if email and "@" not in email:
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


@app.delete(
    "/api/activities/{activity_id}/participants/{student_id}",
    status_code=204,
)
def remove_activity_participant(
    activity_id: int,
    student_id: str,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    """
    นำนักศึกษาออกจากกิจกรรมนี้ (ลบแค่ activity_members)
    ข้อมูลนักศึกษา (students) และกิจกรรมอื่นของนักศึกษายังอยู่
    """
    require_activity(
        db,
        activity_id,
        admin,
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

    ensure_can_access_student(admin, db.get(Student, student_id))

    db.delete(member)
    db.commit()

    return None


# ============================================================
# EXTERNAL ACTIVITIES (ส่งโดยนักศึกษา อนุมัติโดย admin)
# ============================================================


EXTERNAL_ACTIVITY_REQUEST_TYPE = "external_activity"
EXTERNAL_ACTIVITY_REQUEST_LABEL = "External Activity"

EVIDENCE_MAX_BYTES = 5 * 1024 * 1024
EVIDENCE_MAX_FILES = 10

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
    x_student_email: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Student:
    # ยังไม่มีระบบ login นักศึกษา: frontend ส่ง student ID จำลองมาใน header
    # เปลี่ยนเป็นอ่านจาก session/token เมื่อมีระบบ login จริง
    #
    # หน้า /student/login ให้เลือก mock student จากอีเมล (เหมือนแอดมิน) ส่งมาเป็น
    # X-Student-Email แทน X-Student-Id -- ต้องเป็นนักศึกษาที่มีอยู่จริงในตาราง
    # students เท่านั้น (ไม่ auto-create เหมือน path X-Student-Id ด้านล่าง)
    email = (x_student_email or "").strip().lower()

    if email:
        # mock student สาขาเดียวกันใช้อีเมลร่วมกัน: หลัง login frontend ส่ง
        # X-Student-Id มาด้วย ใช้ระบุตัวคนให้ตรง (อีเมลต้องตรงกับคนนั้นด้วย)
        query = db.query(Student).filter(func.lower(func.trim(Student.email)) == email)
        student_id = (x_student_id or "").strip()

        if student_id:
            query = query.filter(Student.student_id == student_id)

        student = query.order_by(Student.student_id).first()

        if not student:
            raise HTTPException(
                status_code=401,
                detail="ไม่พบนักศึกษาตามอีเมลนี้ (X-Student-Email)",
            )

        return student

    student_id = (x_student_id or "").strip()

    if not student_id:
        raise HTTPException(
            status_code=401,
            detail="ไม่พบข้อมูลนักศึกษา (X-Student-Id)",
        )

    student = db.get(Student, student_id)

    if not student:
        # Demo/bypass mode: ยังไม่มีระบบ login นักศึกษาจริง ถ้า student ตาม
        # X-Student-Id ยังไม่มีในระบบ ให้สร้าง mock student ให้อัตโนมัติ
        # เพื่อให้ยิง flow นี้ (เช่น submit external activity) ได้ทันทีตอนเดโม
        student = Student(
            student_id=student_id,
            first_name="Demo",
            last_name="Student",
            email="",
            faculty="Faculty of Science",
            major="",
        )

        db.add(student)
        db.commit()
        db.refresh(student)

    return student


@app.get("/api/student/me")
def get_student_me(
    student: Student = Depends(get_current_student),
):
    return serialize_student_account(student)


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


def validate_evidence_count(count: int) -> None:
    if count < 1:
        raise HTTPException(
            status_code=400,
            detail="กรุณาแนบไฟล์หลักฐานอย่างน้อย 1 ไฟล์",
        )

    if count > EVIDENCE_MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"แนบไฟล์หลักฐานได้สูงสุด {EVIDENCE_MAX_FILES} ไฟล์ต่อคำขอ",
        )


def submitted_evidence(files: list[UploadFile] | None) -> list[UploadFile]:
    # multipart ที่ไม่ได้เลือกไฟล์อาจส่ง part ว่างมา ตัดทิ้งก่อนนับ
    return [file for file in (files or []) if file is not None and file.filename]


async def read_evidence_files(files: list[UploadFile]) -> list[dict]:
    # ตรวจครบทุกไฟล์ก่อนเขียนลงดิสก์ ไฟล์ไหนผิดก็ไม่รับทั้งคำขอ
    return [await read_evidence_file(file) for file in files]


def evidence_folder(external_activity_id: int) -> Path:
    return EXTERNAL_ACTIVITY_UPLOAD_DIR / str(int(external_activity_id))


def evidence_candidate_paths(external_activity_id: int, stored_name: str) -> list[Path]:
    # ที่ใหม่: uploads/<id>/<ไฟล์> ถ้ายังไม่ได้รัน migrate_evidence_files.py
    # ไฟล์ของคำขอเก่าจะยังอยู่ uploads/ ชั้นบน ใช้ .name กันหลุดออกนอกโฟลเดอร์
    name = Path(stored_name).name
    return [
        evidence_folder(external_activity_id) / name,
        EXTERNAL_ACTIVITY_UPLOAD_DIR / name,
    ]


def find_evidence_path(evidence: ExternalActivityEvidence) -> Path | None:
    for path in evidence_candidate_paths(
        evidence.external_activity_id,
        evidence.stored_name,
    ):
        if path.is_file():
            return path

    return None


def remove_evidence_storage(external_activity_id: int, stored_name: str) -> None:
    for path in evidence_candidate_paths(external_activity_id, stored_name):
        path.unlink(missing_ok=True)


def write_evidence_files(
    external_activity_id: int,
    evidence_files: list[dict],
) -> list[Path]:
    folder = evidence_folder(external_activity_id)
    folder.mkdir(parents=True, exist_ok=True)

    written = []
    try:
        for evidence_file in evidence_files:
            path = folder / evidence_file["stored_name"]
            path.write_bytes(evidence_file["contents"])
            written.append(path)
    except Exception:
        remove_written_files(written)
        raise

    return written


def remove_written_files(paths: list[Path]) -> None:
    for path in paths:
        path.unlink(missing_ok=True)

    # ลบโฟลเดอร์ถ้าว่าง (คำขอใหม่ที่บันทึกไม่สำเร็จ)
    for folder in {path.parent for path in paths}:
        try:
            folder.rmdir()
        except OSError:
            pass


def evidence_rows(evidence_files: list[dict]) -> list[ExternalActivityEvidence]:
    return [
        ExternalActivityEvidence(
            stored_name=evidence_file["stored_name"],
            original_name=evidence_file["original_name"],
            content_type=evidence_file["content_type"],
            size=len(evidence_file["contents"]),
        )
        for evidence_file in evidence_files
    ]


def serialize_evidence_file(
    external_activity_id: int,
    evidence: ExternalActivityEvidence,
) -> dict:
    return {
        "id": evidence.id,
        "original_name": evidence.original_name,
        "content_type": evidence.content_type,
        "size": evidence.size,
        "url": f"/api/external-activities/{external_activity_id}/evidence/{evidence.id}",
    }


def serialize_evidence_files(external_activity: ExternalActivity) -> list[dict]:
    return [
        serialize_evidence_file(external_activity.id, evidence)
        for evidence in external_activity.evidence_files
    ]


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
    evidence_files = serialize_evidence_files(external_activity)

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
        "evidence_files": evidence_files,
        # ไฟล์แรก คงไว้ให้โค้ดที่ยังอ่าน evidence แบบไฟล์เดียวใช้ต่อได้
        "evidence": evidence_files[0] if evidence_files else None,
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
    evidence: list[UploadFile] | None = File(None),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    uploads = submitted_evidence(evidence)
    validate_evidence_count(len(uploads))

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
    evidence_files = await read_evidence_files(uploads)
    written_paths: list[Path] = []

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
        # ต้องได้ id ก่อน เพราะไฟล์อยู่ในโฟลเดอร์ uploads/<id>/
        db.flush()

        written_paths = write_evidence_files(external_activity.id, evidence_files)
        external_activity.evidence_files = evidence_rows(evidence_files)

        db.commit()
    except Exception:
        db.rollback()
        remove_written_files(written_paths)
        raise

    db.refresh(external_activity)

    return serialize_external_activity(external_activity)


@app.put("/api/student/me/external-activities/{external_activity_id}")
async def update_external_activity(
    external_activity_id: int,
    title: str = Form(...),
    organization: str = Form(...),
    activity_type: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    location: str = Form(...),
    role: str = Form(...),
    description: str = Form(""),
    skills: str = Form(...),
    evidence: list[UploadFile] | None = File(None),
    remove_evidence_ids: list[int] | None = Form(None),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    แก้ไขกิจกรรมภายนอกที่ถูกไม่อนุมัติ แล้วส่งใหม่ (status กลับเป็น pending)
    evidence = ไฟล์ที่เพิ่มใหม่, remove_evidence_ids = id ไฟล์เดิมที่จะลบ
    ไฟล์เดิมที่ไม่ได้ลบใช้ต่อ รวมแล้วต้องมี 1-10 ไฟล์
    """
    external_activity = db.get(ExternalActivity, external_activity_id)

    if (
        not external_activity
        or external_activity.student_id != student.student_id
    ):
        raise HTTPException(
            status_code=404,
            detail="ไม่พบกิจกรรมภายนอกนี้",
        )

    if external_activity.status != "rejected":
        raise HTTPException(
            status_code=400,
            detail="แก้ไขได้เฉพาะกิจกรรมที่ไม่ได้รับการอนุมัติเท่านั้น",
        )

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

    target_role, related_skills = parse_submitted_skills(skills, role)

    uploads = submitted_evidence(evidence)
    remove_ids = set(remove_evidence_ids or [])
    current_ids = {item.id for item in external_activity.evidence_files}

    if not remove_ids <= current_ids:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์หลักฐานที่จะลบไม่ใช่ของคำขอนี้",
        )

    validate_evidence_count(len(current_ids - remove_ids) + len(uploads))

    new_evidence_files = await read_evidence_files(uploads)

    removed_files = [
        (item.external_activity_id, item.stored_name)
        for item in external_activity.evidence_files
        if item.id in remove_ids
    ]
    written_paths: list[Path] = []

    try:
        external_activity.title = title.strip()
        external_activity.organization = organization.strip()
        external_activity.activity_type = activity_type.strip()
        external_activity.start_date = start_date
        external_activity.end_date = end_date
        external_activity.location = location.strip()
        external_activity.role = role
        external_activity.description = description.strip()

        external_activity.status = "pending"
        external_activity.reject_reason = None
        external_activity.decided_at = None
        external_activity.submitted_at = datetime.now()

        written_paths = write_evidence_files(external_activity.id, new_evidence_files)

        # cascade="all, delete-orphan": แถวที่เอาออกจาก list จะถูกลบ
        external_activity.evidence_files = [
            item
            for item in external_activity.evidence_files
            if item.id not in remove_ids
        ] + evidence_rows(new_evidence_files)

        # cascade="all, delete-orphan" ทำให้ของเก่าถูกลบและแทนที่ด้วยชุดใหม่
        external_activity.skill_levels = [
            ExternalActivitySkill(
                skill_key=skill_key,
                target_role=target_role,
                level=level,
            )
            for skill_key, level in related_skills.items()
        ]

        db.commit()
    except Exception:
        db.rollback()
        remove_written_files(written_paths)
        raise

    # ลบไฟล์เดิมที่ผู้ใช้เอาออก หลัง commit สำเร็จแล้วเท่านั้น
    for activity_id, stored_name in removed_files:
        remove_evidence_storage(activity_id, stored_name)

    db.refresh(external_activity)

    return serialize_external_activity(external_activity)


@app.delete(
    "/api/student/me/external-activities/{external_activity_id}",
    status_code=204,
)
def delete_external_activity(
    external_activity_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    ลบคำขอกิจกรรมภายนอกของตัวเอง ได้เฉพาะ pending หรือ rejected
    approved แล้วนับเข้าทักษะไปแล้ว จึงห้ามลบ
    ลบไฟล์หลักฐานออกจาก uploads หลัง commit สำเร็จ
    """
    external_activity = db.get(ExternalActivity, external_activity_id)

    if (
        not external_activity
        or external_activity.student_id != student.student_id
    ):
        raise HTTPException(
            status_code=404,
            detail="ไม่พบกิจกรรมภายนอกนี้",
        )

    if external_activity.status not in ("pending", "rejected"):
        raise HTTPException(
            status_code=400,
            detail="ลบได้เฉพาะคำขอที่รออนุมัติหรือไม่ได้รับการอนุมัติเท่านั้น",
        )

    activity_id = external_activity.id
    stored_names = [item.stored_name for item in external_activity.evidence_files]
    # คอลัมน์เดิม (เลิกใช้แล้ว) อาจยังชี้ไฟล์ที่ uploads/ ชั้นบน
    if external_activity.evidence_filename:
        stored_names.append(external_activity.evidence_filename)

    # FK ของ notifications เป็น ON DELETE CASCADE ใน PostgreSQL อยู่แล้ว
    # ลบเองด้วยเพื่อให้ผลเหมือนกันทุก DB
    db.query(Notification).filter(
        Notification.external_activity_id == external_activity.id
    ).delete(synchronize_session=False)
    db.delete(external_activity)
    db.commit()

    for stored_name in stored_names:
        remove_evidence_storage(activity_id, stored_name)
    shutil.rmtree(evidence_folder(activity_id), ignore_errors=True)

    return None


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


def create_notification(
    db: Session,
    *,
    student_id: str,
    title: str,
    message: str,
    status: str,
    source: str,
    external_activity_id: int | None = None,
    request_id: int | None = None,
) -> None:
    db.add(
        Notification(
            student_id=student_id,
            source=source,
            external_activity_id=external_activity_id,
            request_id=request_id,
            title=title,
            message=message,
            status=status,
        )
    )


def serialize_notification(notification: Notification) -> dict:
    return {
        "id": notification.id,
        # activityId เป็น id ของตารางตาม source (external_activities หรือ student_requests)
        "source": notification.source,
        "activityId": notification.external_activity_id or notification.request_id,
        "title": notification.title,
        "message": notification.message,
        "status": notification.status,
        "read": notification.is_read,
    }


@app.get("/api/student/me/notifications")
def list_my_notifications(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.student_id == student.student_id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [serialize_notification(item) for item in notifications]


@app.patch("/api/student/me/notifications/mark-all-read")
def mark_all_notifications_read(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.student_id == student.student_id,
        Notification.is_read.is_(False),
    ).update({"is_read": True})

    db.commit()

    return {"updated": True}


@app.patch("/api/student/me/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    notification = db.get(Notification, notification_id)

    if not notification or notification.student_id != student.student_id:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบการแจ้งเตือนนี้",
        )

    notification.is_read = True
    db.commit()

    return serialize_notification(notification)


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
                "evidence_files": [],
            }
        )

    approved_external = (
        db.query(ExternalActivity)
        .filter(
            ExternalActivity.student_id == student.student_id,
            counted_external_activity_filter(),
        )
        .all()
    )

    for external_activity in approved_external:
        evidence_files = serialize_evidence_files(external_activity)
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
                    evidence_files[0]["url"] if evidence_files else None
                ),
                "evidence_files": evidence_files,
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



def faculty_skill_average_for_period(
    db: Session,
    year: int,
    semester: int | None,
    track: str = "participant",
) -> dict:
    """
    ค่าเฉลี่ยทักษะของคณะ ใช้หลักเดียวกับหน้า Admin:
    activity evidence -> ค่าเฉลี่ยต่อ skill ของนักศึกษาแต่ละคน
    -> ค่าเฉลี่ยของนักศึกษาทั้งหมดในคณะ/ระบบ

    ทำแบบ student-first เพื่อไม่ให้นักศึกษาที่มีกิจกรรมเยอะ
    มีน้ำหนักมากกว่าคนอื่น
    """
    member_role = SKILL_TRACKS[track]["member_role"]
    target_role = SKILL_TRACKS[track]["target_role"]
    definitions = SKILL_TRACKS[track]["definitions"]
    grouped: dict[str, dict[str, list[float]]] = {}

    def add_value(student_id, when, skill_key, level):
        if when is None or when.year != year:
            return
        if skill_key not in definitions:
            return

        sem_no = 1 if when.month <= 6 else 2
        if semester is not None and sem_no != semester:
            return

        if student_id not in grouped:
            grouped[student_id] = {
                key: []
                for key in definitions
            }

        grouped[student_id][skill_key].append(float(level))

    internal_rows = (
        db.query(
            Student.student_id,
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
            ActivityMember.role == member_role,
            ActivitySkill.target_role == target_role,
            counted_activity_filter(),
            func.extract("year", Activity.start_at) == year,
        )
        .all()
    )

    external_rows = (
        db.query(
            Student.student_id,
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
            counted_external_activity_filter(),
            ExternalActivity.role == member_role,
            ExternalActivitySkill.target_role == target_role,
            func.extract("year", ExternalActivity.start_date) == year,
        )
        .all()
    )

    for student_id, when, skill_key, level in internal_rows:
        add_value(student_id, when, skill_key, level)

    for student_id, when, skill_key, level in external_rows:
        add_value(student_id, when, skill_key, level)

    return student_first_average(grouped, definitions)


def scoped_skill_average_for_period(
    db: Session,
    year: int,
    semester: int | None,
    track: str,
    major: str | None,
) -> dict:
    """
    ค่าเฉลี่ยทักษะแบบ student-first เหมือน faculty_skill_average_for_period
    แต่นับเฉพาะกิจกรรมในขอบเขตเดียว (ไม่นับกิจกรรมภายนอก):

    major=None  -> กิจกรรมของคณะ (Activity.major เป็น None) ของนักศึกษาทุกคน
    major="เคมี" -> กิจกรรมของสาขาเคมี เฉพาะนักศึกษาสาขาเคมี
    """
    member_role = SKILL_TRACKS[track]["member_role"]
    target_role = SKILL_TRACKS[track]["target_role"]
    definitions = SKILL_TRACKS[track]["definitions"]

    query = (
        db.query(
            Student.student_id,
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
            ActivityMember.role == member_role,
            ActivitySkill.target_role == target_role,
            counted_activity_filter(),
            func.extract("year", Activity.start_at) == year,
        )
    )

    if major is None:
        query = query.filter(faculty_activity_filter())
    else:
        query = query.filter(
            major_activity_filter(major),
            func.trim(Student.major) == major,
        )

    grouped: dict[str, dict[str, list[float]]] = {}

    for student_id, when, skill_key, level in query.all():
        if when is None or skill_key not in definitions:
            continue

        sem_no = 1 if when.month <= 6 else 2
        if semester is not None and sem_no != semester:
            continue

        grouped.setdefault(
            student_id,
            {key: [] for key in definitions},
        )[skill_key].append(float(level))

    return student_first_average(grouped, definitions)


def student_skill_periods(
    student: Student,
    db: Session,
    track: str = "participant",
) -> dict:
    """
    สร้างข้อมูล My Skills จาก source เดียวกันทั้ง Radar และตาราง

    Period ที่สร้าง:
    - year-YYYY       = รวมทั้งปี
    - semester-1-YYYY = ม.ค.-มิ.ย.
    - semester-2-YYYY = ก.ค.-ธ.ค.

    คะแนนแต่ละ skill = ค่าเฉลี่ย level ของกิจกรรมทั้งหมดใน period
    ที่ให้ skill นั้นกับ role ของ track (participant หรือ organizer -> staff skills)
    """
    member_role = SKILL_TRACKS[track]["member_role"]
    target_role = SKILL_TRACKS[track]["target_role"]
    definitions = SKILL_TRACKS[track]["definitions"]
    student_major = (student.major or "").strip()

    activity_map: dict[tuple[str, int], dict] = {}

    # กิจกรรมที่สร้างโดย Admin:
    # นับเฉพาะกรณีที่บทบาทของนักศึกษาและ skill ตรงกับ track
    # และไม่นับกิจกรรมที่ถูกยกเลิก (cancelled)
    rows = (
        db.query(
            Activity.id,
            Activity.name,
            Activity.description,
            Activity.start_at,
            Activity.status,
            Activity.major,
            ActivitySkill.skill_key,
            ActivitySkill.level,
        )
        .join(
            ActivityMember,
            ActivityMember.activity_id == Activity.id,
        )
        .join(
            ActivitySkill,
            ActivitySkill.activity_id == Activity.id,
        )
        .filter(
            ActivityMember.student_id == student.student_id,
            ActivityMember.role == member_role,
            ActivitySkill.target_role == target_role,
            counted_activity_filter(),
        )
        .all()
    )

    for (
        activity_id,
        title,
        description,
        start_at,
        status,
        activity_major,
        skill_key,
        level,
    ) in rows:
        if start_at is None or skill_key not in definitions:
            continue

        key = ("activity", activity_id)

        if key not in activity_map:
            activity_map[key] = {
                "source": "activity",
                "id": activity_id,
                "title": title,
                "description": description or "",
                "start_at": start_at,
                "status": status,
                # other_major ไม่นับเข้ากราฟเปรียบเทียบทั้งสองแบบ (ดู activity_source)
                "scope": activity_source(activity_major, student_major),
                "skills": {},
            }

        activity_map[key]["skills"][skill_key] = int(level)

    # กิจกรรมภายนอก:
    # นับเฉพาะ approved + บทบาทตรงกับ track เท่านั้น
    external_rows = (
        db.query(
            ExternalActivity.id,
            ExternalActivity.title,
            ExternalActivity.description,
            ExternalActivity.start_date,
            ExternalActivity.status,
            ExternalActivitySkill.skill_key,
            ExternalActivitySkill.level,
        )
        .join(
            ExternalActivitySkill,
            ExternalActivitySkill.external_activity_id == ExternalActivity.id,
        )
        .filter(
            ExternalActivity.student_id == student.student_id,
            counted_external_activity_filter(),
            ExternalActivity.role == member_role,
            ExternalActivitySkill.target_role == target_role,
        )
        .all()
    )

    for (
        external_id,
        title,
        description,
        start_date,
        status,
        skill_key,
        level,
    ) in external_rows:
        if start_date is None or skill_key not in definitions:
            continue

        key = ("external_activity", external_id)

        if key not in activity_map:
            activity_map[key] = {
                "source": "external_activity",
                "id": external_id,
                "title": title,
                "description": description or "",
                "start_at": datetime.combine(
                    start_date,
                    datetime.min.time(),
                ),
                "status": status,
                "scope": "external",
                "skills": {},
            }

        activity_map[key]["skills"][skill_key] = int(level)

    activities = sorted(
        activity_map.values(),
        key=lambda item: (
            item["start_at"],
            item["source"],
            item["id"],
        ),
        reverse=True,
    )

    years = sorted(
        {item["start_at"].year for item in activities},
        reverse=True,
    )

    if not years:
        years = [datetime.now().year]

    period_definitions = []
    periods = {}

    for year in years:
        period_definitions.extend(
            [
                {
                    "key": f"year-{year}",
                    "label": f"Year {year}",
                    "year": year,
                    "semester": None,
                },
                {
                    "key": f"semester-1-{year}",
                    "label": f"Semester 1/{year}",
                    "year": year,
                    "semester": 1,
                },
                {
                    "key": f"semester-2-{year}",
                    "label": f"Semester 2/{year}",
                    "year": year,
                    "semester": 2,
                },
            ]
        )

    for period in period_definitions:
        period_activities = []

        for activity in activities:
            activity_year = activity["start_at"].year
            activity_semester = (
                1 if activity["start_at"].month <= 6 else 2
            )

            if activity_year != period["year"]:
                continue

            if (
                period["semester"] is not None
                and activity_semester != period["semester"]
            ):
                continue

            period_activities.append(activity)

        skills = average_activity_skills(period_activities, definitions)

        faculty_average = faculty_skill_average_for_period(
            db=db,
            year=period["year"],
            semester=period["semester"],
            track=track,
        )

        # กราฟเปรียบเทียบแยก 2 แบบ (ไม่นับกิจกรรมภายนอกและกิจกรรมของสาขาอื่น)
        # major:   กิจกรรมสาขาของฉัน   vs ค่าเฉลี่ยนักศึกษาสาขาเดียวกัน
        # faculty: กิจกรรมของคณะของฉัน vs ค่าเฉลี่ยนักศึกษาทั้งคณะ
        comparisons = {
            "major": {
                "skills": average_activity_skills(
                    [a for a in period_activities if a["scope"] == "major"],
                    definitions,
                ),
                "average": (
                    scoped_skill_average_for_period(
                        db,
                        period["year"],
                        period["semester"],
                        track,
                        student_major,
                    )
                    if student_major
                    else {skill_key: None for skill_key in definitions}
                ),
            },
            "faculty": {
                "skills": average_activity_skills(
                    [a for a in period_activities if a["scope"] == "faculty"],
                    definitions,
                ),
                "average": scoped_skill_average_for_period(
                    db,
                    period["year"],
                    period["semester"],
                    track,
                    None,
                ),
            },
        }

        periods[period["key"]] = {
            "key": period["key"],
            "label": period["label"],
            "year": period["year"],
            "semester": period["semester"],
            "skills": skills,
            "facultyAverage": faculty_average,
            "comparisons": comparisons,
            "activities": period_activities,
        }

    current_year = datetime.now().year
    default_period = (
        f"year-{current_year}"
        if f"year-{current_year}" in periods
        else period_definitions[0]["key"]
    )

    return {
        "periodDefinitions": period_definitions,
        "defaultPeriod": default_period,
        "periods": periods,
    }


@app.get("/api/student/me/skills")
def get_my_skills(
    track: str = "participant",
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    My Skills ของนักศึกษาที่ login อยู่

    Radar + ตารางกิจกรรมใช้ source เดียวกัน จึงไม่มีกรณี
    กิจกรรมถูกนำไปคำนวณแต่ไม่ปรากฏในตาราง

    track=participant (ค่าเริ่มต้น) หรือ staff (skill จากการเป็นผู้จัด)
    """
    track = normalize_skill_track(track)
    period_data = student_skill_periods(student, db, track)

    return {
        "student": {
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "faculty": student.faculty,
            "major": student.major,
        },
        "track": track,
        "skillDefinitions": [
            {
                "key": key,
                "label": label,
            }
            for key, label in SKILL_TRACKS[track]["definitions"].items()
        ],
        **period_data,
    }


def skill_pdf_font_name() -> str:
    """
    พยายามใช้ Unicode font จากเครื่องก่อน เพื่อรองรับชื่อ/กิจกรรมภาษาไทย
    ถ้าไม่มีจะ fallback เป็น Helvetica
    """
    candidates = [
        # Docker image: fonts-tlwg-loma-ttf (มีทั้งไทยและอังกฤษ ส่วน NotoSansThai มีแต่อักษรไทย)
        Path("/usr/share/fonts/truetype/tlwg/Loma.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansThai-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]

    for font_path in candidates:
        if font_path.is_file():
            try:
                pdfmetrics.registerFont(
                    TTFont("SkillTranscriptFont", str(font_path))
                )
                return "SkillTranscriptFont"
            except Exception:
                continue

    return "Helvetica"


def build_skill_radar_pdf(
    skills: dict,
    font_name: str,
    faculty_skills: dict | None = None,
    definitions: dict | None = None,
) -> Drawing:
    """
    Radar chart สำหรับ PDF transcript
    ใช้ 6 skill definitions ชุดเดียวกับหน้า Student (participant หรือ staff)
    """
    width = 150 * mm
    height = 92 * mm
    drawing = Drawing(width, height)

    center_x = width / 2
    center_y = height / 2 - 2 * mm
    radius = 31 * mm

    skill_items = list((definitions or PARTICIPANT_SKILL_DEFINITIONS).items())
    count = len(skill_items)

    # Grid 1-5
    for level in range(1, 6):
        level_radius = radius * (level / 5)
        points = []

        for index in range(count):
            angle = math.radians(-90 + index * (360 / count))
            points.extend(
                [
                    center_x + math.cos(angle) * level_radius,
                    center_y + math.sin(angle) * level_radius,
                ]
            )

        drawing.add(
            Polygon(
                points,
                fillColor=None,
                strokeColor=colors.HexColor("#D8E1EF"),
                strokeWidth=0.7,
            )
        )

    # Axis + labels
    for index, (skill_key, label) in enumerate(skill_items):
        angle = math.radians(-90 + index * (360 / count))
        axis_x = center_x + math.cos(angle) * radius
        axis_y = center_y + math.sin(angle) * radius

        drawing.add(
            Line(
                center_x,
                center_y,
                axis_x,
                axis_y,
                strokeColor=colors.HexColor("#E4EAF3"),
                strokeWidth=0.6,
            )
        )

        label_radius = radius + 10 * mm
        label_x = center_x + math.cos(angle) * label_radius
        label_y = center_y + math.sin(angle) * label_radius

        drawing.add(
            String(
                label_x,
                label_y,
                label,
                fontName=font_name,
                fontSize=6.5,
                fillColor=colors.HexColor("#43536F"),
                textAnchor="middle",
            )
        )

    # Faculty average polygon
    if faculty_skills:
        faculty_points = []

        for index, (skill_key, _) in enumerate(skill_items):
            value = faculty_skills.get(skill_key)
            ratio = (
                0
                if value is None
                else max(0, min(5, float(value))) / 5
            )
            angle = math.radians(
                -90 + index * (360 / count)
            )
            faculty_points.extend([
                center_x + math.cos(angle) * radius * ratio,
                center_y + math.sin(angle) * radius * ratio,
            ])

        drawing.add(
            Polygon(
                faculty_points,
                fillColor=colors.Color(
                    16 / 255,
                    185 / 255,
                    129 / 255,
                    alpha=0.08,
                ),
                strokeColor=colors.HexColor("#10B981"),
                strokeWidth=1.4,
                strokeDashArray=[4, 3],
            )
        )

    # Student polygon
    radar_points = []

    for index, (skill_key, _) in enumerate(skill_items):
        value = skills.get(skill_key)
        ratio = 0 if value is None else max(0, min(5, float(value))) / 5
        angle = math.radians(-90 + index * (360 / count))

        point_x = center_x + math.cos(angle) * radius * ratio
        point_y = center_y + math.sin(angle) * radius * ratio

        radar_points.extend([point_x, point_y])

        drawing.add(
            Circle(
                point_x,
                point_y,
                1.3 * mm,
                fillColor=colors.HexColor("#356FE5"),
                strokeColor=colors.white,
                strokeWidth=0.5,
            )
        )

    drawing.add(
        Polygon(
            radar_points,
            fillColor=colors.Color(
                53 / 255,
                111 / 255,
                229 / 255,
                alpha=0.18,
            ),
            strokeColor=colors.HexColor("#356FE5"),
            strokeWidth=1.6,
        )
    )

    return drawing


def escape_pdf_text(value: str) -> str:
    """ข้อความจากผู้ใช้ก่อนใส่ Paragraph ของ ReportLab (ซึ่งอ่านเป็น markup)

    ไม่ escape แล้วชื่อกิจกรรมอย่าง <img src="..."> จะอ่านไฟล์ / เรียก URL จากเซิร์ฟเวอร์
    และแท็กที่ไม่ครบ (<b>x) ทำให้สร้าง PDF ไม่ได้
    """
    return xml_escape(str(value))


@app.get("/api/student/me/skills/export")
def export_my_skills_pdf(
    period: str | None = None,
    include_chart: bool = True,
    track: str = "participant",
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    สร้าง PDF ตาม period และโหมด skill (track) ที่หน้า Student เลือกอยู่

    include_chart=true  -> transcript พร้อม Radar Chart
    include_chart=false -> transcript แบบตาราง ไม่มี Radar Chart
    """
    track = normalize_skill_track(track)
    definitions = SKILL_TRACKS[track]["definitions"]
    period_data = student_skill_periods(student, db, track)
    selected_key = period or period_data["defaultPeriod"]
    selected = period_data["periods"].get(selected_key)

    if selected is None:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบปี/ภาคเรียนที่ต้องการ Export",
        )

    buffer = BytesIO()
    font_name = skill_pdf_font_name()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Skill Transcript - {selected['label']}",
        author="Faculty of Science Student Progress Tracker",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SkillTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17356F"),
    )

    body_style = ParagraphStyle(
        "SkillBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#344054"),
    )

    small_style = ParagraphStyle(
        "SkillSmall",
        parent=body_style,
        fontSize=8,
        leading=10,
    )

    story = [
        Paragraph("Student Skill Transcript", title_style),
        Spacer(1, 3 * mm),
        Paragraph(
            escape_pdf_text(
                f"{student.first_name} {student.last_name} "
                f"| ID: {student.student_id} "
                f"| Period: {selected['label']} "
                f"| {SKILL_TRACKS[track]['label']}"
            ),
            body_style,
        ),
        Spacer(1, 4 * mm),
    ]

    # Optional radar chart
    if include_chart:
        story.append(
            build_skill_radar_pdf(
                selected["skills"],
                font_name,
                selected.get("facultyAverage", {}),
                definitions,
            )
        )
        story.append(Spacer(1, 4 * mm))

    skill_rows = [["Skill", "Average / 5"]]

    for skill_key, label in definitions.items():
        value = selected["skills"].get(skill_key)

        skill_rows.append(
            [
                Paragraph(escape_pdf_text(label), body_style),
                "-" if value is None else f"{value:.2f}",
            ]
        )

    skill_table = Table(
        skill_rows,
        colWidths=[95 * mm, 30 * mm],
        repeatRows=1,
    )
    skill_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17356F")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8DEEA")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(skill_table)
    story.append(Spacer(1, 7 * mm))
    story.append(Paragraph("Activities used for calculation", body_style))
    story.append(Spacer(1, 2 * mm))

    activity_rows = [["Activity", "Skills", "Date", "Status"]]

    for activity in selected["activities"]:
        skills_text = ", ".join(
            (
                f"{definitions.get(key, key)} "
                f"{level}/5"
            )
            for key, level in activity["skills"].items()
        )

        activity_rows.append(
            [
                Paragraph(escape_pdf_text(activity["title"] or "-"), small_style),
                Paragraph(escape_pdf_text(skills_text or "-"), small_style),
                activity["start_at"].strftime("%d/%m/%Y"),
                activity["status"] or "-",
            ]
        )

    if not selected["activities"]:
        activity_rows.append(
            [
                Paragraph("No activity data available", small_style),
                "-",
                "-",
                "-",
            ]
        )

    activity_table = Table(
        activity_rows,
        colWidths=[85 * mm, 110 * mm, 32 * mm, 30 * mm],
        repeatRows=1,
    )
    activity_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17356F")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8DEEA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(activity_table)
    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    safe_period = selected_key.replace("/", "-")
    chart_suffix = "with-radar" if include_chart else "without-radar"

    filename = (
        f"skill-transcript-{student.student_id}-"
        f"{safe_period}-{chart_suffix}.pdf"
    )

    # Content-Length ช่วยให้ browser/download manager รู้ขนาดไฟล์ครบ
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
        },
    )


# ============================================================
# TRANSCRIPT PDF (ดู transcript_data.py / transcript_pdf.py / transcript_config.py)
# ============================================================


def parse_year_levels(years: str | None) -> list[int] | None:
    if not years or not years.strip():
        return None

    try:
        return [int(item) for item in years.split(",") if item.strip()]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="years ต้องเป็นตัวเลขชั้นปีคั่นด้วย comma เช่น 1,2",
        )


@app.get("/api/student/me/transcript/options")
def get_my_transcript_options(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    counts = transcript_data.scope_counts(db, student)

    return {
        "current_year_level": transcript_data.current_year_level(student.student_id),
        "allowed_year_levels": transcript_data.allowed_year_levels(student.student_id),
        "major": (student.major or "").strip(),
        "scopes": [
            {"key": key, "label": label, "count": counts[key]}
            for key, label in transcript_data.SCOPE_LABELS.items()
        ],
        "styles": [
            {"key": key, "label": style["label"]}
            for key, style in TRANSCRIPT_STYLES.items()
        ],
    }


@app.get("/api/student/me/transcript/export")
def export_my_transcript(
    style: str = "A",
    scope: str = "all",
    years: str | None = None,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if style not in TRANSCRIPT_STYLES:
        raise HTTPException(status_code=400, detail="style ต้องเป็น A หรือ B")

    try:
        data = transcript_data.collect_transcript(
            db,
            student,
            scope=scope,
            year_levels=parse_year_levels(years),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    pdf_bytes = render_transcript_pdf(data, style)
    filename = f"transcript-{student.student_id}-{style}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
        },
    )


@app.get("/api/external-activities/{external_activity_id}")
def get_external_activity(
    external_activity_id: int,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    external_activity = require_external_activity(db, external_activity_id)
    ensure_can_access_student(admin, external_activity.student)

    return serialize_external_activity(external_activity)


def ensure_can_view_evidence(
    external_activity: ExternalActivity,
    admin: AdminContext | None,
    x_student_id: str | None,
) -> None:
    # ไฟล์หลักฐานเปิดได้ทั้งแอดมิน (ตามสาขา) และนักศึกษาเจ้าของคำขอ
    if admin is not None:
        ensure_can_access_student(admin, external_activity.student)
        return

    student_id = (x_student_id or "").strip()

    if not student_id:
        raise HTTPException(
            status_code=401,
            detail="ต้องระบุแอดมิน (X-Admin-Email) หรือนักศึกษา (X-Student-Id)",
        )

    if student_id != external_activity.student_id:
        raise HTTPException(
            status_code=403,
            detail="เปิดได้เฉพาะไฟล์หลักฐานของคำขอตัวเอง",
        )


def evidence_file_response(evidence: ExternalActivityEvidence) -> FileResponse:
    path = find_evidence_path(evidence)

    if path is None:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบไฟล์หลักฐาน",
        )

    return FileResponse(
        path,
        media_type=evidence.content_type,
        filename=evidence.original_name,
        content_disposition_type="inline",
    )


@app.get("/api/external-activities/{external_activity_id}/evidence")
def get_external_activity_evidence(
    external_activity_id: int,
    db: Session = Depends(get_db),
    admin: AdminContext | None = Depends(get_optional_admin),
    x_student_id: str | None = Header(default=None),
):
    # URL เดิมแบบไฟล์เดียว: ส่งไฟล์แรกของคำขอ
    external_activity = require_external_activity(
        db,
        external_activity_id,
    )
    ensure_can_view_evidence(external_activity, admin, x_student_id)

    if not external_activity.evidence_files:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบไฟล์หลักฐาน",
        )

    return evidence_file_response(external_activity.evidence_files[0])


@app.get("/api/external-activities/{external_activity_id}/evidence/{evidence_id}")
def get_external_activity_evidence_file(
    external_activity_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
    admin: AdminContext | None = Depends(get_optional_admin),
    x_student_id: str | None = Header(default=None),
):
    evidence = db.get(ExternalActivityEvidence, evidence_id)

    if not evidence or evidence.external_activity_id != external_activity_id:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบไฟล์หลักฐาน",
        )

    ensure_can_view_evidence(evidence.external_activity, admin, x_student_id)

    return evidence_file_response(evidence)


class ExternalActivityDecision(BaseModel):
    # skill levels นักศึกษาตั้งมาตั้งแต่ตอนส่งแล้ว admin แค่อนุมัติ/ไม่อนุมัติ
    status: str
    reject_reason: str | None = None


@app.patch("/api/external-activities/{external_activity_id}/decision")
def decide_external_activity(
    external_activity_id: int,
    payload: ExternalActivityDecision,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
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
    ensure_can_access_student(admin, external_activity.student)

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

        create_notification(
            db,
            student_id=external_activity.student_id,
            title=external_activity.title,
            message=reject_reason,
            status="Rejected",
            source="external_activity",
            external_activity_id=external_activity.id,
        )

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
    reject_reason: str | None = None


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
        "reject_reason": request.reject_reason,
        "submitted_at": request.submitted_at,
        "decided_at": request.decided_at,
    }


@app.get("/api/requests/stats")
def get_request_stats(
    major: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    # major: แอดมินกลางเลือก filter สาขาได้จากหน้า Approvals (ดู resolve_branch_filter)
    admin = resolve_branch_filter(admin, major)

    today_start = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    total_pending = (
        scope_student_request_query(db.query(func.count(StudentRequest.id)), admin)
        .filter(StudentRequest.status == "pending")
        .scalar()
        or 0
    )

    approved_today = (
        scope_student_request_query(db.query(func.count(StudentRequest.id)), admin)
        .filter(
            StudentRequest.status == "approved",
            StudentRequest.decided_at >= today_start,
        )
        .scalar()
        or 0
    )

    rejected_today = (
        scope_student_request_query(db.query(func.count(StudentRequest.id)), admin)
        .filter(
            StudentRequest.status == "rejected",
            StudentRequest.decided_at >= today_start,
        )
        .scalar()
        or 0
    )

    # รวมกิจกรรมภายนอกเข้าไปในตัวเลขของหน้า Approvals ด้วย
    total_pending += (
        scope_external_activity_query(db.query(func.count(ExternalActivity.id)), admin)
        .filter(ExternalActivity.status == "pending")
        .scalar()
        or 0
    )

    approved_today += (
        scope_external_activity_query(db.query(func.count(ExternalActivity.id)), admin)
        .filter(
            ExternalActivity.status == "approved",
            ExternalActivity.decided_at >= today_start,
        )
        .scalar()
        or 0
    )

    rejected_today += (
        scope_external_activity_query(db.query(func.count(ExternalActivity.id)), admin)
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
    major: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminContext = Depends(get_current_admin),
):
    # รวม 2 แหล่ง (student_requests + external_activities) แล้วเรียง/แบ่งหน้าใน Python
    # ปริมาณคำขอยังน้อย ถ้าเยอะขึ้นควรย้ายไปทำ UNION ใน SQL
    # major: แอดมินกลางเลือก filter สาขาได้จากหน้า Approvals (ดู resolve_branch_filter)
    admin = resolve_branch_filter(admin, major)

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
        query = scope_student_request_query(db.query(StudentRequest), admin)

        if status:
            query = query.filter(StudentRequest.status == status)

        if request_type:
            query = query.filter(StudentRequest.request_type == request_type)

        items.extend(serialize_request(item) for item in query.all())

    if include_external:
        query = scope_external_activity_query(db.query(ExternalActivity), admin)

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
    admin: AdminContext = Depends(get_current_admin),
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

    ensure_can_access_student(
        admin,
        db.get(Student, request.requester_student_id),
    )

    if request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="คำขอนี้ถูกดำเนินการไปแล้ว",
        )

    if payload.status == "rejected":
        reject_reason = (payload.reject_reason or "").strip()

        if not reject_reason:
            raise HTTPException(
                status_code=400,
                detail="กรุณาระบุเหตุผลที่ไม่อนุมัติ",
            )

        request.reject_reason = reject_reason

        create_notification(
            db,
            student_id=request.requester_student_id,
            title=request.detail
            or REQUEST_TYPE_DEFINITIONS.get(
                request.request_type,
                request.request_type,
            ),
            message=reject_reason,
            status="Rejected",
            source="student_request",
            request_id=request.id,
        )
    else:
        request.reject_reason = None

    request.status = payload.status
    request.decided_at = datetime.now()

    db.commit()
    db.refresh(request)

    return serialize_request(request)