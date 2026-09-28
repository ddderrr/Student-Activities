from datetime import date

import pytest

from models import ExternalActivity, ExternalActivitySkill, Notification, Student

STUDENT_ID = "670510659"
HEADERS = {"X-Student-Id": STUDENT_ID}


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


def create_activity(db_session, upload_dir, status, student_id=STUDENT_ID) -> ExternalActivity:
    activity = ExternalActivity(
        student_id=student_id,
        title="Volunteer Camp",
        organization="Some NGO",
        activity_type="จิตอาสา / บริการสังคม",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 10),
        location="Chiang Mai",
        role="participant",
        evidence_filename=f"{status}-{student_id}.png",
        evidence_original_name="evidence.png",
        evidence_content_type="image/png",
        evidence_size=4,
        status=status,
        reject_reason="ไม่ชัดเจน" if status == "rejected" else None,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    db_session.add(
        ExternalActivitySkill(
            external_activity_id=activity.id,
            skill_key="volunteerism",
            target_role="participant",
            level=3,
        )
    )
    db_session.commit()

    (upload_dir / activity.evidence_filename).write_bytes(b"test")
    return activity


@pytest.mark.parametrize("status", ["pending", "rejected"])
def test_student_can_delete_pending_or_rejected_request(client, db_session, upload_dir, status):
    create_student(db_session)
    activity = create_activity(db_session, upload_dir, status)
    activity_id = activity.id
    evidence_path = upload_dir / activity.evidence_filename

    response = client.delete(
        f"/api/student/me/external-activities/{activity_id}",
        headers=HEADERS,
    )

    assert response.status_code == 204
    db_session.expire_all()
    assert db_session.get(ExternalActivity, activity_id) is None
    assert (
        db_session.query(ExternalActivitySkill)
        .filter_by(external_activity_id=activity_id)
        .count()
        == 0
    )
    assert not evidence_path.exists()


def test_cannot_delete_approved_request(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_activity(db_session, upload_dir, "approved")
    evidence_path = upload_dir / activity.evidence_filename

    response = client.delete(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
    )

    assert response.status_code == 400
    db_session.expire_all()
    assert db_session.get(ExternalActivity, activity.id) is not None
    assert evidence_path.exists()


def test_cannot_delete_another_students_request(client, db_session, upload_dir):
    create_student(db_session)
    create_student(db_session, student_id="670510000")
    activity = create_activity(db_session, upload_dir, "pending", student_id="670510000")
    evidence_path = upload_dir / activity.evidence_filename

    response = client.delete(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
    )

    assert response.status_code == 404
    db_session.expire_all()
    assert db_session.get(ExternalActivity, activity.id) is not None
    assert evidence_path.exists()


def test_delete_unknown_request_returns_404(client, db_session, upload_dir):
    create_student(db_session)

    response = client.delete(
        "/api/student/me/external-activities/999999",
        headers=HEADERS,
    )

    assert response.status_code == 404


def test_delete_removes_notifications_of_that_request(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_activity(db_session, upload_dir, "rejected")
    db_session.add(
        Notification(
            student_id=STUDENT_ID,
            source="external_activity",
            external_activity_id=activity.id,
            title="Volunteer Camp",
            message="ไม่ชัดเจน",
            status="Rejected",
        )
    )
    db_session.commit()

    response = client.delete(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
    )

    assert response.status_code == 204
    notifications = client.get("/api/student/me/notifications", headers=HEADERS)
    assert notifications.json() == []


def test_delete_succeeds_when_evidence_file_already_missing(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_activity(db_session, upload_dir, "pending")
    (upload_dir / activity.evidence_filename).unlink()

    response = client.delete(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
    )

    assert response.status_code == 204
