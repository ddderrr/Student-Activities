from datetime import date, datetime

from models import Activity, ActivityMember, ExternalActivity, Student


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
    db_session.refresh(student)
    return student


def create_activity_with_member(db_session, student_id, start_at, role="participant") -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name=f"Activity {start_at.isoformat()}",
        start_at=start_at,
        end_at=start_at,
        responsible_person="Staff",
        location="Room 1",
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    db_session.add(
        ActivityMember(
            activity_id=activity.id,
            student_id=student_id,
            role=role,
        )
    )
    db_session.commit()

    return activity


def create_external_activity(db_session, student_id, start_date, **overrides) -> ExternalActivity:
    defaults = dict(
        student_id=student_id,
        title=f"External {start_date.isoformat()}",
        organization="Some Org",
        activity_type="Workshop",
        start_date=start_date,
        end_date=start_date,
        location="Online",
        role="participant",
        description="",
        evidence_filename="evidence.png",
        evidence_original_name="evidence.png",
        evidence_content_type="image/png",
        evidence_size=100,
        status="approved",
    )
    defaults.update(overrides)

    activity = ExternalActivity(**defaults)
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def test_months_param_narrows_participants_and_activities_to_that_month(client, db_session):
    student_a = create_student(db_session, "670510001")
    student_b = create_student(db_session, "670510002")

    create_activity_with_member(db_session, student_a.student_id, datetime(2026, 3, 15))
    create_external_activity(db_session, student_b.student_id, date(2026, 5, 20))

    march_only = client.get("/api/admin/dashboard?year=2026&months=3").json()
    assert march_only["totalActivities"] == 1
    assert march_only["totalParticipants"] == 1

    may_only = client.get("/api/admin/dashboard?year=2026&months=5").json()
    assert may_only["totalActivities"] == 1
    assert may_only["totalParticipants"] == 1

    both_months = client.get("/api/admin/dashboard?year=2026&months=3,5").json()
    assert both_months["totalActivities"] == 2
    assert both_months["totalParticipants"] == 2

    april_only = client.get("/api/admin/dashboard?year=2026&months=4").json()
    assert april_only["totalActivities"] == 0
    assert april_only["totalParticipants"] == 0


def test_months_param_overrides_semester_param(client, db_session):
    student = create_student(db_session, "670510003")
    create_external_activity(db_session, student.student_id, date(2026, 7, 10))

    # semester=SEMESTER_1 (Jan-Jun) would normally exclude a July activity,
    # but an explicit months= should take priority over the semester bucket.
    response = client.get(
        "/api/admin/dashboard?year=2026&semester=SEMESTER_1&months=7"
    ).json()

    assert response["totalActivities"] == 1
    assert response["totalParticipants"] == 1


def test_months_param_rejects_invalid_values(client):
    assert client.get("/api/admin/dashboard?months=abc").status_code == 400
    assert client.get("/api/admin/dashboard?months=13").status_code == 400
    assert client.get("/api/admin/dashboard?months=0").status_code == 400
