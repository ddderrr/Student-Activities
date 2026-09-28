from datetime import datetime

from models import Activity

CS = "วิทยาการคอมพิวเตอร์"
CS_ADMIN = {"X-Admin-Email": "cs@test.local"}


def create_activity(db_session, major=CS, name="Faculty Activity") -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name=name,
        start_at=datetime(2026, 4, 1, 9, 0, 0),
        end_at=datetime(2026, 4, 1, 12, 0, 0),
        responsible_person="Staff",
        location="Room 1",
        major=major,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def test_student_sees_faculty_activity_after_admin_adds_them_as_participant(
    client, db_session
):
    """
    รีเกรสชันของ Task: "กิจกรรมคณะ" ไม่ขึ้นในหน้านักศึกษาหลัง admin เพิ่มเป็น
    participant. ครอบคลุม flow เต็ม: admin เพิ่มผ่าน participants/import/confirm
    (endpoint เดียวกับที่ฟอร์ม Add Participant มือเรียก) -> นักศึกษาเรียก
    /api/student/me/activities ต้องเห็นกิจกรรมนั้นในฐานะ ActivityMember
    """
    activity = create_activity(db_session, major=CS, name="CS Faculty Activity")

    confirm_response = client.post(
        f"/api/activities/{activity.id}/participants/import/confirm",
        headers=CS_ADMIN,
        json={
            "students": [
                {
                    "student_id": "670510101",
                    "first_name": "สมชาย",
                    "last_name": "ใจดี",
                    "email": "670510101@test.local",
                    "major": CS,
                    "role": "participant",
                }
            ]
        },
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["imported_count"] == 1

    student_response = client.get(
        "/api/student/me/activities",
        headers={"X-Student-Id": "670510101"},
    )
    assert student_response.status_code == 200

    data = student_response.json()
    assert data["total"] == 1
    assert data["activities"][0]["id"] == activity.id
    assert data["activities"][0]["source"] == "activity"
    assert data["activities"][0]["title"] == "CS Faculty Activity"


def test_student_with_no_memberships_sees_no_faculty_activities(client, db_session):
    create_activity(db_session, major=CS, name="Someone Else's Activity")

    student_response = client.get(
        "/api/student/me/activities",
        headers={"X-Student-Id": "670510102"},
    )
    assert student_response.status_code == 200
    assert student_response.json()["total"] == 0
