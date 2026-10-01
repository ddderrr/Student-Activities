from datetime import datetime

from models import Activity, ActivityMember, Student
from tests.conftest import CS_ADMIN_EMAIL
from tests.test_students_import_legacy_xls import (
    XLS_CONTENT_TYPE,
    build_legacy_xls,
)

CS_ADMIN_HEADERS = {"X-Admin-Email": CS_ADMIN_EMAIL}


def create_activity(db_session) -> Activity:
    activity = Activity(
        activity_type="Volunteer",
        name="Test Activity",
        start_at=datetime(2026, 1, 10, 9, 0, 0),
        end_at=datetime(2026, 1, 10, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def preview(client, activity_id, content, filename="checkin.xls"):
    return client.post(
        f"/api/activities/{activity_id}/participants/import/preview",
        files={"file": (filename, content, XLS_CONTENT_TYPE)},
    )


def confirm(client, activity_id, students):
    return client.post(
        f"/api/activities/{activity_id}/participants/import/confirm",
        json={"students": students},
    )


def test_preview_legacy_xls_parses_without_requiring_email(client, db_session):
    activity = create_activity(db_session)

    content = build_legacy_xls(
        [
            [1, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"],
        ]
    )

    response = preview(client, activity.id, content)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["invalid_count"] == 0
    assert body["invalid_rows"] == []

    student = body["students"][0]
    assert student["student_id"] == "670510670"
    assert student["first_name"] == "จักริน"
    assert student["last_name"] == "ชวชาติ"
    assert student["email"] == ""
    assert student["faculty"] == "คณะวิทยาศาสตร์"
    assert student["role"] == "participant"


def test_preview_legacy_xls_rejects_wrong_columns(client, db_session):
    activity = create_activity(db_session)

    content = build_legacy_xls(
        [[1, "670510670", "จักริน ชวชาติ", "10:05:00"]],
        headers=["ลำดับ", "รหัสนักศึกษา", "ชื่อ", "เวลา"],
    )

    response = preview(client, activity.id, content)

    assert response.status_code == 400
    assert "faculty" in response.json()["detail"]


def test_confirm_legacy_xls_creates_student_and_membership_with_blank_email(
    client,
    db_session,
):
    activity = create_activity(db_session)

    content = build_legacy_xls(
        [
            [1, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"],
        ]
    )

    preview_response = preview(client, activity.id, content)
    assert preview_response.status_code == 200

    students = preview_response.json()["students"]

    confirm_response = confirm(client, activity.id, students)

    assert confirm_response.status_code == 200

    student = db_session.get(Student, "670510670")
    assert student is not None
    assert student.first_name == "จักริน"
    assert student.last_name == "ชวชาติ"
    assert student.email == ""
    assert student.faculty == "Faculty of Science"

    membership = (
        db_session.query(ActivityMember)
        .filter_by(
            activity_id=activity.id,
            student_id="670510670",
        )
        .one_or_none()
    )
    assert membership is not None
    assert membership.role == "participant"


def test_update_participant_role_without_email_after_import(
    client,
    db_session,
):
    activity = create_activity(db_session)

    content = build_legacy_xls(
        [
            [1, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"],
        ]
    )

    students = preview(client, activity.id, content).json()["students"]
    confirm(client, activity.id, students)

    student = db_session.get(Student, "670510670")
    assert student.email == ""

    response = client.patch(
        f"/api/activities/{activity.id}/participants/670510670",
        json={
            "first_name": "จักริน",
            "last_name": "ชวชาติ",
            "email": "",
            "faculty": "คณะวิทยาศาสตร์",
            "major": "",
            "role": "organizer",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "organizer"
    assert body["email"] == ""

    membership = (
        db_session.query(ActivityMember)
        .filter_by(
            activity_id=activity.id,
            student_id="670510670",
        )
        .one_or_none()
    )
    assert membership.role == "organizer"


def test_branch_admin_import_legacy_xls_keeps_students_visible_to_self(
    client,
    db_session,
):
    # กิจกรรมของคณะเห็นร่วมกันทุกแอดมิน แต่รายชื่อผู้เข้าร่วม (Student.major)
    # ถูกกรองด้วย scope_student_query จึงต้องเช็คว่านักศึกษาที่เพิ่งถูก
    # import ด้วยไฟล์ .xls (ไม่มี column major) ยังเห็นได้โดยแอดมินสาขาที่
    # เป็นคน import เอง ไม่ใช่หลุดออกจาก scope ของตัวเอง
    activity = create_activity(db_session)

    content = build_legacy_xls(
        [
            [1, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"],
        ]
    )

    preview_response = client.post(
        f"/api/activities/{activity.id}/participants/import/preview",
        files={"file": ("checkin.xls", content, XLS_CONTENT_TYPE)},
        headers=CS_ADMIN_HEADERS,
    )
    assert preview_response.status_code == 200
    students = preview_response.json()["students"]

    confirm_response = client.post(
        f"/api/activities/{activity.id}/participants/import/confirm",
        json={"students": students},
        headers=CS_ADMIN_HEADERS,
    )
    assert confirm_response.status_code == 200

    student = db_session.get(Student, "670510670")
    assert student is not None
    assert student.major == "วิทยาการคอมพิวเตอร์"

    participants_response = client.get(
        f"/api/activities/{activity.id}/participants",
        headers=CS_ADMIN_HEADERS,
    )
    assert participants_response.status_code == 200

    visible_ids = {
        item["student_id"]
        for item in participants_response.json()["students"]
    }
    assert "670510670" in visible_ids
