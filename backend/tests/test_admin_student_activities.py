from datetime import date, datetime

from models import Activity, ActivityMember, ExternalActivity, Student


def create_student(db_session, student_id="670510670") -> Student:
    student = Student(
        student_id=student_id,
        first_name="จักริน",
        last_name="ชวชาติ",
        email="jakkarin@cmu.ac.th",
        faculty="คณะวิทยาศาสตร์",
        major="",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def create_faculty_activity(db_session, student_id, role="participant") -> Activity:
    activity = Activity(
        activity_type="Volunteer",
        name="Faculty Activity",
        start_at=datetime(2026, 1, 10, 9, 0, 0),
        end_at=datetime(2026, 1, 10, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
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


def create_external_activity(
    db_session,
    student_id,
    status="approved",
    role="participant",
    title="External Activity",
) -> ExternalActivity:
    external_activity = ExternalActivity(
        student_id=student_id,
        title=title,
        organization="Some Org",
        activity_type="Workshop",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 2),
        location="Online",
        role=role,
        description="",
        evidence_filename="evidence.pdf",
        evidence_original_name="evidence.pdf",
        evidence_content_type="application/pdf",
        evidence_size=1024,
        status=status,
    )
    db_session.add(external_activity)
    db_session.commit()
    db_session.refresh(external_activity)
    return external_activity


def test_get_admin_student_activities_returns_404_for_unknown_student(client):
    response = client.get("/api/admin/students/000000000/activities")

    assert response.status_code == 404


def test_get_admin_student_activities_combines_faculty_and_all_external_statuses(
    client,
    db_session,
):
    student = create_student(db_session)

    create_faculty_activity(db_session, student.student_id, role="organizer")
    create_external_activity(
        db_session,
        student.student_id,
        status="approved",
        title="Approved External",
    )
    create_external_activity(
        db_session,
        student.student_id,
        status="pending",
        title="Pending External",
    )
    create_external_activity(
        db_session,
        student.student_id,
        status="rejected",
        title="Rejected External",
    )

    response = client.get(
        f"/api/admin/students/{student.student_id}/activities"
    )

    assert response.status_code == 200
    body = response.json()

    assert body["student"]["student_id"] == student.student_id
    assert body["total"] == 4

    by_title = {item["title"]: item for item in body["activities"]}

    assert by_title["Faculty Activity"]["source"] == "activity"
    assert by_title["Faculty Activity"]["role"] == "organizer"
    assert by_title["Faculty Activity"]["status"] == "approved"

    assert by_title["Approved External"]["source"] == "external_activity"
    assert by_title["Approved External"]["status"] == "approved"

    assert by_title["Pending External"]["status"] == "pending"
    assert by_title["Rejected External"]["status"] == "rejected"


def test_get_admin_student_activities_empty_for_student_with_no_activities(
    client,
    db_session,
):
    student = create_student(db_session, student_id="670510999")

    response = client.get(
        f"/api/admin/students/{student.student_id}/activities"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["activities"] == []
