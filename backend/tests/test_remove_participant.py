from datetime import datetime

from models import Activity, ActivityMember, Student


def create_student(db_session, student_id) -> Student:
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
    return student


def create_activity(db_session, name, member_ids) -> Activity:
    activity = Activity(
        activity_type="Volunteer",
        name=name,
        start_at=datetime(2026, 1, 10, 9, 0, 0),
        end_at=datetime(2026, 1, 10, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
    )
    db_session.add(activity)
    db_session.commit()

    for student_id in member_ids:
        db_session.add(
            ActivityMember(
                activity_id=activity.id,
                student_id=student_id,
                role="participant",
            )
        )

    db_session.commit()
    return activity


def participant_ids(client, activity_id):
    response = client.get(f"/api/activities/{activity_id}/participants")
    assert response.status_code == 200
    return [student["student_id"] for student in response.json()["students"]]


def test_remove_participant_only_removes_that_membership(client, db_session):
    create_student(db_session, "670510001")
    create_student(db_session, "670510002")

    activity = create_activity(db_session, "Activity A", ["670510001", "670510002"])
    other_activity = create_activity(db_session, "Activity B", ["670510001"])

    response = client.delete(
        f"/api/activities/{activity.id}/participants/670510001"
    )

    assert response.status_code == 204
    assert participant_ids(client, activity.id) == ["670510002"]

    # ข้อมูลนักศึกษาและกิจกรรมอื่นต้องยังอยู่
    assert participant_ids(client, other_activity.id) == ["670510001"]

    db_session.expire_all()
    assert db_session.get(Student, "670510001") is not None


def test_remove_participant_not_in_activity_returns_404(client, db_session):
    create_student(db_session, "670510001")
    activity = create_activity(db_session, "Activity A", [])

    response = client.delete(
        f"/api/activities/{activity.id}/participants/670510001"
    )

    assert response.status_code == 404


def test_remove_participant_unknown_activity_returns_404(client):
    response = client.delete("/api/activities/9999/participants/670510001")

    assert response.status_code == 404
