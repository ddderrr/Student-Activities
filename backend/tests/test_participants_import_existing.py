"""ตารางตรวจสอบก่อนนำเข้าผู้ร่วมกิจกรรม: บอกว่ารหัสไหนอยู่ในกิจกรรมนี้แล้ว ("มีอยู่แล้ว")

POST /api/activities/{id}/participants/import/existing คืนเฉพาะรหัสที่ส่งมาและเป็นสมาชิกแล้ว
(นับทุกสาขา เพราะ confirm ก็ข้ามคนเหล่านี้เป็นข้อมูลซ้ำเหมือนกัน)
"""

from datetime import datetime

from models import Activity, ActivityMember, Student
from tests.conftest import CHEM_ADMIN_EMAIL, CS_ADMIN_EMAIL

CHEM = "เคมี"
CS = "วิทยาการคอมพิวเตอร์"


def create_activity(db_session, major=None) -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name="Activity",
        start_at=datetime(2026, 1, 10, 9, 0, 0),
        end_at=datetime(2026, 1, 10, 12, 0, 0),
        responsible_person="Staff",
        location="Room 1",
        major=major,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def add_student(db_session, activity, student_id, major):
    db_session.add(Student(student_id=student_id, first_name="A", last_name="B", email="", faculty="", major=major))
    if activity is not None:
        db_session.add(ActivityMember(activity_id=activity.id, student_id=student_id, role="participant"))
    db_session.commit()


def existing(client, activity_id, student_ids, admin_email=None):
    headers = {"X-Admin-Email": admin_email} if admin_email else {}
    return client.post(
        f"/api/activities/{activity_id}/participants/import/existing",
        json={"student_ids": student_ids},
        headers=headers,
    )


def test_returns_only_requested_ids_that_are_members(client, db_session):
    activity = create_activity(db_session)
    add_student(db_session, activity, "670510001", CHEM)
    add_student(db_session, activity, "670510002", CS)
    add_student(db_session, None, "670510003", CHEM)

    response = existing(client, activity.id, ["670510001", " 670510003 ", "670510009"])

    assert response.status_code == 200, response.text
    assert response.json() == {"existing_ids": ["670510001"]}


def test_branch_admin_sees_members_from_other_branches_in_faculty_activity(client, db_session):
    activity = create_activity(db_session)
    add_student(db_session, activity, "670510002", CS)

    response = existing(client, activity.id, ["670510002"], CHEM_ADMIN_EMAIL)

    assert response.json() == {"existing_ids": ["670510002"]}


def test_branch_admin_cannot_check_other_branch_activity(client, db_session):
    activity = create_activity(db_session, major=CHEM)

    response = existing(client, activity.id, ["670510001"], CS_ADMIN_EMAIL)

    assert response.status_code == 403
