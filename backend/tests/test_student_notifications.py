"""แจ้งเตือนนักศึกษาเมื่อคำขอกิจกรรมภายนอกได้รับการอนุมัติ / ไม่อนุมัติ"""

from models import Notification
from tests.test_notifications_and_bypass import create_external_activity, create_student

STUDENT = {"X-Student-Id": "670510659"}
URL = "/api/student/me/notifications"


def decide(client, activity_id, **payload):
    response = client.patch(f"/api/external-activities/{activity_id}/decision", json=payload)
    assert response.status_code == 200
    return response


def test_approval_notifies_student_with_link_and_type(client, db_session):
    create_student(db_session)
    activity = create_external_activity(db_session)

    decide(client, activity.id, status="approved")

    [item] = client.get(URL, headers=STUDENT).json()["notifications"]
    assert item["type"] == "approved"
    assert item["status"] == "Approved"
    assert item["title"] == "Volunteer Camp"
    assert item["message"] == ""
    assert item["read"] is False
    assert item["link"] == f"/student/activities?open={activity.id}"
    assert item["createdAt"].endswith("+07:00")


def test_rejection_notifies_student_with_reason(client, db_session):
    create_student(db_session)
    activity = create_external_activity(db_session)

    decide(client, activity.id, status="rejected", reject_reason="หลักฐานไม่ชัดเจน")

    [item] = client.get(URL, headers=STUDENT).json()["notifications"]
    assert item["type"] == "rejected"
    assert item["message"] == "หลักฐานไม่ชัดเจน"
    assert item["link"] == f"/student/activities?open={activity.id}"


def test_newest_first_and_read_all(client, db_session):
    create_student(db_session)
    first = create_external_activity(db_session)
    second = create_external_activity(db_session)
    decide(client, first.id, status="rejected", reject_reason="ขาดหลักฐาน")
    decide(client, second.id, status="approved")

    items = client.get(URL, headers=STUDENT).json()["notifications"]
    assert [item["type"] for item in items] == ["approved", "rejected"]

    assert client.patch(f"{URL}/{items[0]['id']}/read", headers=STUDENT).json()["read"] is True
    assert [item["read"] for item in client.get(URL, headers=STUDENT).json()["notifications"]] == [True, False]

    assert client.patch(f"{URL}/read-all", headers=STUDENT).status_code == 200
    assert all(item["read"] for item in client.get(URL, headers=STUDENT).json()["notifications"])


def test_students_only_see_their_own_notifications(client, db_session):
    create_student(db_session)
    create_student(db_session, "670510700")
    activity = create_external_activity(db_session)
    decide(client, activity.id, status="approved")

    other = {"X-Student-Id": "670510700"}
    assert client.get(URL, headers=other).json()["notifications"] == []
    notification_id = db_session.query(Notification).one().id
    assert client.patch(f"{URL}/{notification_id}/read", headers=other).status_code == 404


def test_decided_activity_cannot_notify_twice(client, db_session):
    create_student(db_session)
    activity = create_external_activity(db_session)
    decide(client, activity.id, status="approved")

    again = client.patch(f"/api/external-activities/{activity.id}/decision", json={"status": "approved"})
    assert again.status_code == 400
    assert db_session.query(Notification).count() == 1


def add_notifications(db_session, count, student_id="670510659", is_read=False, created_at=None):
    for index in range(count):
        db_session.add(Notification(
            student_id=student_id, source="external_activity", title=f"Activity {index}",
            message="", status="Approved", is_read=is_read,
            **({"created_at": created_at} if created_at else {}),
        ))
    db_session.commit()


def test_list_is_paged_and_unread_count_covers_everything(client, db_session):
    create_student(db_session)
    add_notifications(db_session, 35)
    add_notifications(db_session, 5, is_read=True)

    first = client.get(URL, headers=STUDENT).json()
    assert len(first["notifications"]) == 30
    assert first["has_more"] is True
    # นับยังไม่อ่านจากทั้งหมด 40 รายการ ไม่ใช่แค่ 30 ที่ส่งมา
    assert first["unread_count"] == 35

    ids = [item["id"] for item in first["notifications"]]
    assert ids == sorted(ids, reverse=True)

    second = client.get(URL, params={"before_id": ids[-1]}, headers=STUDENT).json()
    assert len(second["notifications"]) == 10
    assert second["has_more"] is False
    assert not set(ids) & {item["id"] for item in second["notifications"]}


def test_prune_removes_only_old_read_student_notifications(db_session):
    from datetime import datetime

    from notification_retention import prune_old_notifications

    old = datetime(2026, 1, 1, 9, 0)
    add_notifications(db_session, 2, is_read=True, created_at=old)   # ลบ
    add_notifications(db_session, 1, is_read=False, created_at=old)  # ยังไม่อ่าน เก็บไว้
    add_notifications(db_session, 1, is_read=True)                   # ใหม่ เก็บไว้

    result = prune_old_notifications(db_session, days=90, now=datetime(2026, 10, 5, 9, 0))

    assert result["student"] == 2
    assert db_session.query(Notification).count() == 2
    assert prune_old_notifications(db_session, days=0)["student"] == 0


def test_delete_all_removes_only_my_notifications(client, db_session):
    create_student(db_session)
    create_student(db_session, "670510700")
    add_notifications(db_session, 3)
    add_notifications(db_session, 2, student_id="670510700")

    assert client.delete(URL, headers=STUDENT).json() == {"deleted": 3}

    body = client.get(URL, headers=STUDENT).json()
    assert (body["notifications"], body["unread_count"]) == ([], 0)
    assert db_session.query(Notification).filter_by(student_id="670510700").count() == 2
