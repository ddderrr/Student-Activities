from datetime import datetime

from models import Activity, ActivityMember, Student


def create_student(db_session, student_id) -> Student:
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


def create_activity(db_session, name, status, start_at, participant_ids) -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name=name,
        start_at=start_at,
        end_at=start_at,
        responsible_person="Staff",
        location="Room 1",
        status=status,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    for student_id in participant_ids:
        db_session.add(
            ActivityMember(
                activity_id=activity.id,
                student_id=student_id,
                role="participant",
            )
        )
    db_session.commit()
    return activity


def seed(db_session):
    create_student(db_session, "670000001")
    create_student(db_session, "670000002")
    # เดือน มี.ค. มีกิจกรรมปกติ 1 และ cancelled 1 / เดือน เม.ย. มีแต่ cancelled
    create_activity(db_session, "Active March", "active", datetime(2026, 3, 10, 9), ["670000001"])
    create_activity(db_session, "Cancelled March", "cancelled", datetime(2026, 3, 20, 9), ["670000002"])
    create_activity(db_session, "Cancelled April", "cancelled", datetime(2026, 4, 5, 9), ["670000002"])


def test_total_activities_excludes_cancelled(client, db_session):
    seed(db_session)

    response = client.get("/api/admin/dashboard?year=2026&semester=ALL")

    assert response.status_code == 200
    assert response.json()["totalActivities"] == 1


def test_activity_growth_excludes_cancelled(client, db_session):
    seed(db_session)

    response = client.get("/api/admin/dashboard?year=2026&semester=ALL")

    growth = {item["month"]: item["count"] for item in response.json()["activityGrowth"]}
    assert growth["MAR"] == 1
    assert growth["APR"] == 0


def test_total_participants_excludes_cancelled_activities(client, db_session):
    seed(db_session)

    response = client.get("/api/admin/dashboard?year=2026&semester=ALL")

    # 670000002 อยู่แค่ในกิจกรรม cancelled
    assert response.json()["totalParticipants"] == 1


def test_completion_rate_unchanged_by_cancelled(client, db_session):
    seed(db_session)

    response = client.get("/api/admin/dashboard?year=2026&semester=ALL")

    body = response.json()
    # กิจกรรม active ที่จบไปแล้ว (end_at ผ่านมาแล้ว) นับเป็น completed
    assert body["completionEligibleActivities"] == 1
    assert body["completionRate"] == 100
