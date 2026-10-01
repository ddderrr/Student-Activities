"""ข้อมูลที่ส่งเข้า Transcript PDF ต้องตรงกับ My Skills และไม่มีกิจกรรมที่ถูกยกเลิก

Transcript (transcript_data.collect_transcript) มี query ของตัวเอง ไม่ได้ใช้
student_skill_periods ของหน้า My Skills เทสต์นี้กันไม่ให้สองทางนี้เพี้ยนออกจากกัน
"""

from datetime import date, datetime
from io import BytesIO

import pytest
from pypdf import PdfReader

import main as main_module
import transcript_data
from main import student_skill_periods
from models import (
    Activity,
    ActivityMember,
    ActivitySkill,
    ExternalActivity,
    ExternalActivitySkill,
    Student,
)
from skill_definitions import PARTICIPANT_SKILL_DEFINITIONS

STUDENT_ID = "670510999"
HEADERS = {"X-Student-Id": STUDENT_ID}

# ชื่ออังกฤษ เพื่อให้ตรวจข้อความใน PDF จริงได้ตรง ๆ
CANCELLED_TITLES = {"Cancelled Workshop", "Cancelled Organizer Duty"}
UNAPPROVED_TITLES = {"Pending External Camp", "Rejected External Camp"}


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(transcript_data, "today", lambda: date(2026, 9, 28))


def add_activity(db_session, name, start, status="active", role="participant", skills=None, major=None):
    activity = Activity(
        activity_type="Workshop",
        name=name,
        start_at=start,
        end_at=start.replace(hour=16),
        department="",
        responsible_person="Staff",
        location="SCB1100",
        status=status,
        major=major,
    )
    db_session.add(activity)
    db_session.commit()

    db_session.add(ActivityMember(activity_id=activity.id, student_id=STUDENT_ID, role=role))
    for skill_key, level in (skills or {}).items():
        db_session.add(
            ActivitySkill(
                activity_id=activity.id,
                skill_key=skill_key,
                target_role="participant" if role == "participant" else "staff",
                level=level,
            )
        )
    db_session.commit()
    return activity


def add_external(db_session, title, start, status="approved", skills=None):
    activity = ExternalActivity(
        student_id=STUDENT_ID,
        title=title,
        organization="Some Org",
        activity_type="Workshop",
        start_date=start,
        end_date=start,
        location="Chiang Mai",
        role="participant",
        description="",
        status=status,
    )
    db_session.add(activity)
    db_session.commit()

    for skill_key, level in (skills or {}).items():
        db_session.add(
            ExternalActivitySkill(
                external_activity_id=activity.id,
                skill_key=skill_key,
                target_role="participant",
                level=level,
            )
        )
    db_session.commit()
    return activity


@pytest.fixture()
def student(db_session):
    student = Student(
        student_id=STUDENT_ID,
        first_name="Somying",
        last_name="Demo",
        email="demo@test.local",
        faculty="Faculty of Science",
        major="เคมี",
    )
    db_session.add(student)
    db_session.commit()

    add_activity(db_session, "Faculty Orientation", datetime(2024, 8, 10, 9),
                 skills={"academics": 4, "arts_culture_traditions": 3})
    add_activity(db_session, "Chemistry Camp", datetime(2025, 7, 12, 9), major="เคมี",
                 skills={"academics": 2, "volunteerism": 5}, status="completed")
    add_activity(db_session, "Science Day Staff", datetime(2025, 8, 18, 9), role="organizer",
                 skills={"innovation": 4})
    # ยกเลิกแล้ว (มี skill สูง ๆ ถ้าหลุดเข้ามาค่าเฉลี่ยจะเพี้ยนชัดเจน)
    add_activity(db_session, "Cancelled Workshop", datetime(2025, 9, 1, 9), status="cancelled",
                 skills={"academics": 1, "volunteerism": 1, "health_promotion": 5})
    add_activity(db_session, "Cancelled Organizer Duty", datetime(2026, 7, 2, 9), status="cancelled",
                 role="organizer", skills={"innovation": 1})

    add_external(db_session, "Forest Volunteer", date(2026, 2, 1),
                 skills={"volunteerism": 3, "nature_environmental_conservation": 5})
    add_external(db_session, "Pending External Camp", date(2026, 3, 1), status="pending",
                 skills={"health_promotion": 1})
    add_external(db_session, "Rejected External Camp", date(2026, 3, 2), status="rejected",
                 skills={"health_promotion": 1})

    return student


@pytest.fixture()
def captured(monkeypatch):
    """ดักข้อมูลที่ endpoint ส่งเข้า render_transcript_pdf (ไม่ต้อง render จริง)"""
    calls = []

    def fake_render(data, style, issued_on=None):
        calls.append({"data": data, "style": style})
        return b"%PDF-1.4 fake"

    monkeypatch.setattr(main_module, "render_transcript_pdf", fake_render)
    return calls


def export(client, query="style=A&scope=all"):
    response = client.get(f"/api/student/me/transcript/export?{query}", headers=HEADERS)
    assert response.status_code == 200, response.text
    return response


def transcript_items(data):
    return [item for group in data["groups"] for item in group["activities"]]


def my_skills_all_activities(student, db_session):
    """กิจกรรมทุกช่วงเวลาของ My Skills (รวมทุก period ปี = ไม่ซ้ำ)"""
    periods = student_skill_periods(student, db_session)["periods"]
    activities = {}
    for key, period in periods.items():
        if key.startswith("year-"):
            for activity in period["activities"]:
                activities[(activity["source"], activity["id"])] = activity
    return activities


def average(activities):
    values = {key: [] for key in PARTICIPANT_SKILL_DEFINITIONS}
    for activity in activities:
        for skill_key, level in activity["skills"].items():
            values[skill_key].append(level)
    return {
        key: round(sum(levels) / len(levels), 2) if levels else None
        for key, levels in values.items()
    }


# ------------------------------------------------------------
# ข้อมูลที่ส่งเข้า PDF (ผ่าน endpoint จริง)
# ------------------------------------------------------------


def test_pdf_data_has_no_cancelled_or_unapproved_activities(client, student, captured):
    export(client)

    data = captured[0]["data"]
    titles = {item["title"] for item in transcript_items(data)}

    assert titles == {"Faculty Orientation", "Chemistry Camp", "Science Day Staff", "Forest Volunteer"}
    assert not titles & CANCELLED_TITLES
    assert not titles & UNAPPROVED_TITLES
    # จำนวนกิจกรรมในสรุปก็ไม่นับกิจกรรมที่ยกเลิก
    assert data["summary"]["total"] == 4
    assert data["summary"]["organizer"] == 1
    assert sum(data["summary"]["by_source"].values()) == 4


@pytest.mark.parametrize("scope", ["all", "major", "faculty", "external"])
def test_every_scope_excludes_cancelled(client, student, captured, scope):
    export(client, f"style=B&scope={scope}")

    titles = {item["title"] for item in transcript_items(captured[0]["data"])}
    assert not titles & (CANCELLED_TITLES | UNAPPROVED_TITLES)


def test_pdf_skill_scores_match_my_skills(client, student, captured, db_session):
    export(client)

    data = captured[0]["data"]
    my_skills = my_skills_all_activities(student, db_session)

    # ชุดกิจกรรมที่ให้คะแนนทักษะ ต้องเป็นชุดเดียวกับ My Skills
    transcript_skill_keys = {
        ("activity" if item["key"].startswith("activity-") else "external_activity",
         int(item["key"].split("-", 1)[1]))
        for item in transcript_items(data)
        if item["skills"]
    }
    assert transcript_skill_keys == set(my_skills)

    # คะแนนของแต่ละกิจกรรมตรงกัน
    for item in transcript_items(data):
        if item["skills"]:
            source = "activity" if item["key"].startswith("activity-") else "external_activity"
            key = (source, int(item["key"].split("-", 1)[1]))
            assert item["skills"] == my_skills[key]["skills"]

    # ค่าเฉลี่ยในเอกสาร = ค่าเฉลี่ยจากกิจกรรมทั้งหมดของ My Skills
    assert data["skills"] == average(my_skills.values())
    assert data["skills"]["academics"] == 3.0
    assert data["skills"]["volunteerism"] == 4.0
    assert data["skills"]["health_promotion"] is None  # มีแค่ในกิจกรรมที่ยกเลิก/ไม่อนุมัติ


def test_my_skills_itself_excludes_cancelled(student, db_session):
    titles = {activity["title"] for activity in my_skills_all_activities(student, db_session).values()}

    assert not titles & (CANCELLED_TITLES | UNAPPROVED_TITLES)


def test_options_counts_exclude_cancelled(client, student):
    body = client.get("/api/student/me/transcript/options", headers=HEADERS).json()

    assert {item["key"]: item["count"] for item in body["scopes"]} == {
        "all": 4,
        "major": 1,
        "faculty": 2,
        "external": 1,
    }


# ------------------------------------------------------------
# PDF จริง (render ครบ)
# ------------------------------------------------------------


def pdf_text(content: bytes) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)


@pytest.mark.parametrize("style", ["A", "B"])
def test_rendered_transcript_pdf_has_no_cancelled_activities(client, student, style):
    text = pdf_text(export(client, f"style={style}&scope=all").content)

    for title in {"Faculty Orientation", "Chemistry Camp", "Science Day Staff", "Forest Volunteer"}:
        assert title in text
    for title in CANCELLED_TITLES | UNAPPROVED_TITLES:
        assert title not in text


def test_my_skills_pdf_has_no_cancelled_activities(client, student):
    response = client.get(
        "/api/student/me/skills/export?period=year-2025&include_chart=false",
        headers=HEADERS,
    )

    assert response.status_code == 200
    text = pdf_text(response.content)
    assert "Chemistry Camp" in text
    assert "Cancelled Workshop" not in text
