"""กติกาเดียวของประเภทกิจกรรม (คณะ / สาขา / สาขาอื่น) ใช้ร่วมกันทั้ง My Skills, Student Skills และ Transcript

activities.major ที่เป็นค่าว่างหรือมีช่องว่างหน้า-หลัง ต้องได้ผลเหมือนกันทุกหน้า
"""

from datetime import date, datetime

import pytest

import transcript_data
from models import Activity, ActivityMember, ActivitySkill, Student
from skill_scoring import activity_source
from tests.conftest import CENTRAL_ADMIN_EMAIL

STUDENT_ID = "670510999"
CHEM = "เคมี"


@pytest.mark.parametrize(
    "activity_major, student_major, expected",
    [
        (None, CHEM, "faculty"),
        ("", CHEM, "faculty"),
        ("   ", CHEM, "faculty"),
        (CHEM, CHEM, "major"),
        (f" {CHEM} ", CHEM, "major"),
        (CHEM, f" {CHEM} ", "major"),
        ("ฟิสิกส์", CHEM, "other_major"),
        (CHEM, "", "other_major"),
        (CHEM, None, "other_major"),
        (None, "", "faculty"),
    ],
)
def test_activity_source(activity_major, student_major, expected):
    assert activity_source(activity_major, student_major) == expected


# activities.major -> ทักษะที่กิจกรรมนั้นให้ (คนละทักษะ เพื่อแยกให้ออกว่านับเข้าไหน)
ACTIVITIES = [
    (None, "arts_culture_traditions", 1),
    ("", "volunteerism", 2),
    ("   ", "academics", 3),
    (f" {CHEM} ", "internationalization", 4),
    ("ฟิสิกส์", "health_promotion", 5),
]

FACULTY = {"arts_culture_traditions": 1.0, "volunteerism": 2.0, "academics": 3.0}
MAJOR = {"internationalization": 4.0}


def expected_skills(values):
    keys = [
        "arts_culture_traditions",
        "volunteerism",
        "academics",
        "internationalization",
        "health_promotion",
        "nature_environmental_conservation",
    ]
    return {key: values.get(key) for key in keys}


@pytest.fixture()
def student(db_session, monkeypatch):
    monkeypatch.setattr(transcript_data, "today", lambda: date(2026, 9, 30))

    student = Student(
        student_id=STUDENT_ID,
        first_name="Somying",
        last_name="Demo",
        email="demo@test.local",
        faculty="Faculty of Science",
        major=CHEM,
    )
    db_session.add(student)
    db_session.commit()

    for index, (major, skill_key, level) in enumerate(ACTIVITIES):
        start = datetime(2026, 3, 1 + index, 9)
        activity = Activity(
        activity_hours=3,
            activity_type="Workshop",
            name=f"Activity {index}",
            start_at=start,
            end_at=start.replace(hour=16),
            department="",
            responsible_person="Staff",
            location="SCB1100",
            status="active",
            major=major,
        )
        db_session.add(activity)
        db_session.commit()
        db_session.add(ActivityMember(activity_id=activity.id, student_id=STUDENT_ID, role="participant"))
        db_session.add(
            ActivitySkill(activity_id=activity.id, skill_key=skill_key, target_role="participant", level=level)
        )
        db_session.commit()

    return student


def test_my_skills_comparisons_use_shared_rule(client, student):
    body = client.get("/api/student/me/skills", headers={"X-Student-Id": STUDENT_ID}).json()
    comparisons = body["periods"]["year-2026"]["comparisons"]

    assert comparisons["faculty"]["skills"] == expected_skills(FACULTY)
    assert comparisons["major"]["skills"] == expected_skills(MAJOR)
    # ค่าเฉลี่ยที่ใช้เทียบ (SQL) ต้องใช้กติกาเดียวกับฝั่งนักศึกษา
    assert comparisons["faculty"]["average"] == expected_skills(FACULTY)
    assert comparisons["major"]["average"] == expected_skills(MAJOR)


def test_admin_student_skills_use_shared_rule(client, student):
    body = client.get(
        "/api/admin/student-skills?year=2026",
        headers={"X-Admin-Email": CENTRAL_ADMIN_EMAIL},
    ).json()
    entry = next(item for item in body["students"] if item["id"] == STUDENT_ID)

    assert entry["facultySkills"] == expected_skills(FACULTY)
    assert entry["majorSkills"] == expected_skills(MAJOR)


def test_transcript_uses_shared_rule(db_session, student):
    data = transcript_data.collect_transcript(db_session, student, scope="all")

    assert data["summary"]["by_source"] == {"faculty": 3, "major": 1, "other_major": 1, "external": 0}
    assert {
        item["title"]
        for item in transcript_data.collect_transcript(db_session, student, scope="faculty")["groups"][0]["activities"]
    } == {"Activity 0", "Activity 1", "Activity 2"}
    assert [
        item["title"]
        for item in transcript_data.collect_transcript(db_session, student, scope="major")["groups"][0]["activities"]
    ] == ["Activity 3"]
