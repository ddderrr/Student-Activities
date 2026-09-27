from datetime import datetime

from models import Activity, ActivityMember, ActivitySkill, Student

STUDENT_ID = "670510659"


def create_student(db_session, student_id=STUDENT_ID) -> Student:
    student = Student(
        student_id=student_id,
        first_name="Test",
        last_name="Student",
        email="",
        faculty="Faculty of Science",
        major="",
    )
    db_session.add(student)
    db_session.commit()
    return student


def create_activity_with_skill(
    db_session,
    name,
    status,
    level,
    student_id=STUDENT_ID,
    skill_key="volunteerism",
) -> Activity:
    activity = Activity(
        activity_type="Volunteer",
        name=name,
        start_at=datetime(2026, 3, 10, 9, 0, 0),
        end_at=datetime(2026, 3, 10, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
        status=status,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    db_session.add_all([
        ActivityMember(
            activity_id=activity.id,
            student_id=student_id,
            role="participant",
        ),
        ActivitySkill(
            activity_id=activity.id,
            skill_key=skill_key,
            target_role="participant",
            level=level,
        ),
    ])
    db_session.commit()

    return activity


def seed_active_and_cancelled(db_session):
    create_student(db_session)
    active = create_activity_with_skill(db_session, "Active", "active", level=4)
    cancelled = create_activity_with_skill(db_session, "Cancelled", "cancelled", level=1)
    return active, cancelled


def test_admin_student_skills_ignores_cancelled_activities(client, db_session):
    seed_active_and_cancelled(db_session)

    response = client.get("/api/admin/student-skills?year=2026&semester=ALL")

    assert response.status_code == 200
    students = response.json()["students"]
    assert len(students) == 1
    assert students[0]["skills"]["volunteerism"] == 4.0
    assert students[0]["activityCount"] == 1
    assert students[0]["skillActivityCounts"]["volunteerism"] == 1


def test_admin_student_skills_omits_student_with_only_cancelled_activity(client, db_session):
    create_student(db_session)
    create_activity_with_skill(db_session, "Cancelled", "cancelled", level=2)

    response = client.get("/api/admin/student-skills?year=2026&semester=ALL")

    assert response.status_code == 200
    assert response.json()["students"] == []


def test_my_skills_ignores_cancelled_activities(client, db_session):
    active, _ = seed_active_and_cancelled(db_session)

    response = client.get(
        "/api/student/me/skills",
        headers={"X-Student-Id": STUDENT_ID},
    )

    assert response.status_code == 200
    period = response.json()["periods"]["year-2026"]
    assert period["skills"]["volunteerism"] == 4.0
    assert [item["id"] for item in period["activities"]] == [active.id]


def test_faculty_average_ignores_cancelled_activities(client, db_session):
    seed_active_and_cancelled(db_session)

    response = client.get(
        "/api/student/me/skills",
        headers={"X-Student-Id": STUDENT_ID},
    )

    assert response.status_code == 200
    faculty_average = response.json()["periods"]["year-2026"]["facultyAverage"]
    assert faculty_average["volunteerism"] == 4.0


def create_staff_skill_activity(db_session, name, status, level, start_at, skill_key="innovation") -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name=name,
        start_at=start_at,
        end_at=start_at,
        responsible_person="Staff Name",
        location="Room 101",
        status=status,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    db_session.add(
        ActivitySkill(
            activity_id=activity.id,
            skill_key=skill_key,
            target_role="staff",
            level=level,
        )
    )
    db_session.commit()

    return activity


def test_dashboard_staff_skill_average_ignores_cancelled_activities(client, db_session):
    start_at = datetime(2026, 3, 10, 9, 0, 0)
    create_staff_skill_activity(db_session, "Active", "active", level=5, start_at=start_at)
    create_staff_skill_activity(db_session, "Cancelled", "cancelled", level=1, start_at=start_at)

    response = client.get("/api/admin/dashboard?year=2026&semester=ALL")

    assert response.status_code == 200
    skills = {item["name"]: item["percentage"] for item in response.json()["skills"]}
    # (5 / 5) * 100 = 100; ถ้านับ cancelled ด้วยจะได้ (3 / 5) * 100 = 60
    assert skills["Innovation"] == 100


def test_dashboard_years_exclude_years_with_only_cancelled_activities(client, db_session):
    create_staff_skill_activity(
        db_session, "Active", "active", level=3, start_at=datetime(2024, 3, 10, 9, 0, 0)
    )
    create_staff_skill_activity(
        db_session, "Cancelled", "cancelled", level=3, start_at=datetime(2023, 3, 10, 9, 0, 0)
    )

    response = client.get("/api/admin/dashboard?year=2024&semester=ALL")

    assert response.status_code == 200
    years = response.json()["availableYears"]
    assert 2024 in years
    assert 2023 not in years


def test_admin_student_skills_years_exclude_years_with_only_cancelled_activities(client, db_session):
    create_student(db_session)
    create_activity_with_skill(db_session, "Active", "active", level=4)
    cancelled = create_activity_with_skill(db_session, "Cancelled", "cancelled", level=1)
    cancelled.start_at = datetime(2023, 3, 10, 9, 0, 0)
    cancelled.end_at = datetime(2023, 3, 10, 12, 0, 0)
    db_session.commit()

    response = client.get("/api/admin/student-skills?year=2026&semester=ALL")

    assert response.status_code == 200
    payload = response.json()
    assert 2026 in payload["years"]
    assert 2023 not in payload["years"]
    assert 2023 not in payload["availableYears"]
