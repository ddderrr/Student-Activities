"""
โหมด skill (track): participant = skill จากการเป็นผู้เข้าร่วม, staff = skill จากการเป็นผู้จัด (organizer)
ทั้งหน้า Student Skills (admin) และ My Skills (นักศึกษา)
"""

from datetime import datetime

from main import PARTICIPANT_SKILL_DEFINITIONS, STAFF_SKILL_DEFINITIONS
from models import Activity, ActivityMember, ActivitySkill, Student


def add_student(db_session, student_id, major):
    db_session.add(
        Student(
            student_id=student_id,
            first_name="Test",
            last_name=student_id,
            email=f"{student_id}@test.local",
            faculty="Faculty of Science",
            major=major,
        )
    )


def seed(db_session):
    # 670510001 เป็นผู้จัด, 670510002 เป็นผู้เข้าร่วม ในกิจกรรมเดียวกัน
    add_student(db_session, "670510001", "เคมี")
    add_student(db_session, "670510002", "เคมี")
    add_student(db_session, "670510003", "วิทยาการคอมพิวเตอร์")
    db_session.commit()

    activity = Activity(
        activity_type="Volunteer",
        name="Track Activity",
        start_at=datetime(2026, 8, 1, 9, 0, 0),
        end_at=datetime(2026, 8, 1, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
        skill_levels=[
            ActivitySkill(skill_key="innovation", target_role="staff", level=5),
            ActivitySkill(skill_key="volunteerism", target_role="participant", level=3),
        ],
    )
    db_session.add(activity)
    db_session.commit()

    db_session.add_all([
        ActivityMember(activity_id=activity.id, student_id="670510001", role="organizer"),
        ActivityMember(activity_id=activity.id, student_id="670510002", role="participant"),
    ])
    db_session.commit()


def report(client, track=None, **headers):
    url = "/api/admin/student-skills?year=2026&semester=SEMESTER_2"
    if track:
        url += f"&track={track}"
    return client.get(url, headers=headers or None)


def test_participant_track_is_default_and_only_counts_participants(client, db_session):
    seed(db_session)

    body = report(client).json()

    assert body["track"] == "participant"
    assert [skill["key"] for skill in body["skillDefinitions"]] == list(PARTICIPANT_SKILL_DEFINITIONS)
    assert [student["id"] for student in body["students"]] == ["670510002"]
    assert body["students"][0]["skills"]["volunteerism"] == 3


def test_staff_track_only_counts_organizers_with_staff_skills(client, db_session):
    seed(db_session)

    body = report(client, "staff").json()

    assert body["track"] == "staff"
    assert [skill["key"] for skill in body["skillDefinitions"]] == list(STAFF_SKILL_DEFINITIONS)
    assert len(body["benchmarkScores"]) == len(STAFF_SKILL_DEFINITIONS)
    assert [student["id"] for student in body["students"]] == ["670510001"]
    assert body["students"][0]["skills"]["innovation"] == 5
    assert set(body["students"][0]["skills"]) == set(STAFF_SKILL_DEFINITIONS)


def test_invalid_track_returns_400(client, db_session):
    seed(db_session)

    assert report(client, "coach").status_code == 400


def test_benchmark_is_saved_per_track(client, db_session):
    seed(db_session)

    response = client.put(
        "/api/admin/student-skills/benchmark?track=staff",
        json={"scores": {"innovation": 3.5}},
    )
    assert response.status_code == 200
    assert response.json()["benchmarkBySkill"]["innovation"] == 3.5

    assert report(client, "staff").json()["benchmarkBySkill"]["innovation"] == 3.5
    assert report(client).json()["benchmarkBySkill"]["volunteerism"] == 4.0

    # skill ของอีกโหมดใช้ไม่ได้
    wrong = client.put(
        "/api/admin/student-skills/benchmark?track=staff",
        json={"scores": {"volunteerism": 3}},
    )
    assert wrong.status_code == 400


def test_population_is_scoped_to_the_major_admin(client, db_session):
    seed(db_session)

    body = report(client, **{"X-Admin-Email": "chem@test.local"}).json()

    assert {item["major"] for item in body["population"]} == {"เคมี"}
    assert sum(item["count"] for item in body["population"]) == 2


def test_my_skills_staff_track(client, db_session):
    seed(db_session)

    headers = {"X-Student-Id": "670510001"}

    participant = client.get("/api/student/me/skills", headers=headers).json()
    assert participant["track"] == "participant"
    assert participant["periods"]["year-2026"]["skills"]["volunteerism"] is None

    staff = client.get("/api/student/me/skills?track=staff", headers=headers).json()
    assert staff["track"] == "staff"
    assert [skill["key"] for skill in staff["skillDefinitions"]] == list(STAFF_SKILL_DEFINITIONS)
    assert staff["periods"]["year-2026"]["skills"]["innovation"] == 5
    assert staff["periods"]["year-2026"]["facultyAverage"]["innovation"] == 5

    assert client.get("/api/student/me/skills?track=coach", headers=headers).status_code == 400


def test_export_pdf_staff_track(client, db_session):
    seed(db_session)

    response = client.get(
        "/api/student/me/skills/export?period=year-2026&track=staff",
        headers={"X-Student-Id": "670510001"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
