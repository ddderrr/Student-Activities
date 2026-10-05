"""กระดิ่งแจ้งเตือนฝั่งแอดมิน: นักศึกษาส่ง / ส่งใหม่คำขอกิจกรรมภายนอก -> แอดมินสาขาของ
นักศึกษา + แอดมินกลางเห็น แอดมินสาขาอื่นไม่เห็น สถานะอ่านแล้วแยกต่อแอดมิน
"""

import base64
import json
from datetime import date, datetime, timezone

from models import AdminNotification, ExternalActivity, Student
from tests.conftest import CENTRAL_ADMIN_EMAIL, CHEM_ADMIN_EMAIL, CS_ADMIN_EMAIL

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
CS = "วิทยาการคอมพิวเตอร์"
CHEM = "เคมี"
FORM = {
    "title": "Beach Cleanup",
    "organization": "Green NGO",
    "activity_type": "จิตอาสา / บริการสังคม",
    "start_date": "2026-02-01",
    "end_date": "2026-02-01",
    "location": "Phuket",
    "role": "participant",
    "description": "",
    "skills": json.dumps({"volunteerism": 3}),
}


def make_student(db_session, student_id, major, first="สมชาย"):
    db_session.add(Student(student_id=student_id, first_name=first, last_name="ใจดี",
                           email=f"{student_id}@cmu.ac.th", faculty="Faculty of Science", major=major))
    db_session.commit()


def submit(client, student_id, title="Beach Cleanup"):
    response = client.post(
        "/api/student/me/external-activities",
        headers={"X-Student-Id": student_id},
        data={**FORM, "title": title},
        files={"evidence": ("evidence.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def feed(client, admin_email):
    response = client.get("/api/admin/notifications", headers={"X-Admin-Email": admin_email})
    assert response.status_code == 200
    return response.json()


def test_submission_notifies_own_branch_and_central_only(client, db_session):
    make_student(db_session, "670510101", CS)
    external_id = submit(client, "670510101")

    cs, central, chem = feed(client, CS_ADMIN_EMAIL), feed(client, CENTRAL_ADMIN_EMAIL), feed(client, CHEM_ADMIN_EMAIL)

    assert (cs["unread_count"], central["unread_count"], chem["unread_count"]) == (1, 1, 0)
    item = cs["notifications"][0]
    assert item["type"] == "external_submitted"
    assert (item["student_name"], item["activity_title"], item["is_read"]) == ("สมชาย ใจดี", "Beach Cleanup", False)
    assert item["message"] == "นักศึกษา สมชาย ใจดี ส่งคำขอเพิ่มกิจกรรมภายนอก Beach Cleanup"
    assert item["link"] == f"/admin/approvals?review={external_id}"
    assert datetime.fromisoformat(item["created_at"]).tzinfo is not None
    assert chem["notifications"] == []


def test_student_without_major_only_reaches_central(client, db_session):
    make_student(db_session, "670510102", "")
    submit(client, "670510102")

    assert feed(client, CENTRAL_ADMIN_EMAIL)["unread_count"] == 1
    assert feed(client, CS_ADMIN_EMAIL)["unread_count"] == 0
    assert feed(client, CHEM_ADMIN_EMAIL)["unread_count"] == 0


def test_resubmission_creates_a_resubmitted_notification(client, db_session):
    make_student(db_session, "670510103", CHEM)
    db_session.add(ExternalActivity(student_id="670510103", title="Old", organization="Org",
                                    activity_type="จิตอาสา / บริการสังคม", start_date=date(2026, 1, 10),
                                    end_date=date(2026, 1, 10), location="CM", role="participant",
                                    status="rejected", reject_reason="ไม่ชัดเจน"))
    db_session.commit()
    external_id = db_session.query(ExternalActivity).one().id

    response = client.put(
        f"/api/student/me/external-activities/{external_id}",
        headers={"X-Student-Id": "670510103"},
        data={**FORM, "title": "Fixed Title"},
        files={"evidence": ("evidence.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 200, response.text

    item = feed(client, CHEM_ADMIN_EMAIL)["notifications"][0]
    assert (item["type"], item["activity_title"]) == ("external_resubmitted", "Fixed Title")
    assert "อีกครั้ง" in item["message"]
    assert feed(client, CS_ADMIN_EMAIL)["unread_count"] == 0


def test_read_state_is_per_admin(client, db_session):
    make_student(db_session, "670510101", CS)
    submit(client, "670510101")
    notification_id = feed(client, CS_ADMIN_EMAIL)["notifications"][0]["id"]

    response = client.patch(f"/api/admin/notifications/{notification_id}/read", headers={"X-Admin-Email": CS_ADMIN_EMAIL})
    assert response.status_code == 200
    # กดซ้ำได้ ไม่ error
    assert client.patch(f"/api/admin/notifications/{notification_id}/read", headers={"X-Admin-Email": CS_ADMIN_EMAIL}).status_code == 200

    cs = feed(client, CS_ADMIN_EMAIL)
    assert (cs["unread_count"], cs["notifications"][0]["is_read"]) == (0, True)
    # แอดมินกลางยังไม่ได้อ่าน
    assert feed(client, CENTRAL_ADMIN_EMAIL)["unread_count"] == 1


def test_branch_admin_cannot_mark_other_branch_notification(client, db_session):
    make_student(db_session, "670510101", CS)
    submit(client, "670510101")
    notification_id = feed(client, CS_ADMIN_EMAIL)["notifications"][0]["id"]

    response = client.patch(f"/api/admin/notifications/{notification_id}/read", headers={"X-Admin-Email": CHEM_ADMIN_EMAIL})
    assert response.status_code == 404


def test_read_all_marks_only_this_admins_scope(client, db_session):
    make_student(db_session, "670510101", CS)
    make_student(db_session, "670510201", CHEM)
    submit(client, "670510101", "CS 1")
    submit(client, "670510101", "CS 2")
    submit(client, "670510201", "Chem 1")

    response = client.patch("/api/admin/notifications/read-all", headers={"X-Admin-Email": CS_ADMIN_EMAIL})
    assert response.json() == {"marked": 2}

    assert feed(client, CS_ADMIN_EMAIL)["unread_count"] == 0
    assert feed(client, CHEM_ADMIN_EMAIL)["unread_count"] == 1
    assert feed(client, CENTRAL_ADMIN_EMAIL)["unread_count"] == 3


def test_newest_first(client, db_session):
    make_student(db_session, "670510101", CS)
    for title in ["First", "Second", "Third"]:
        submit(client, "670510101", title)
    db_session.query(AdminNotification).filter_by(activity_title="First").update(
        {"created_at": datetime(2026, 1, 1, tzinfo=timezone.utc)}
    )
    db_session.commit()

    titles = [item["activity_title"] for item in feed(client, CS_ADMIN_EMAIL)["notifications"]]
    assert titles[-1] == "First"
    assert set(titles[:2]) == {"Second", "Third"}


def test_deleting_request_or_student_removes_notifications(client, db_session):
    make_student(db_session, "670510101", CS)
    make_student(db_session, "670510102", CS)
    external_id = submit(client, "670510101", "Will be deleted")
    submit(client, "670510102", "Student will be deleted")

    assert client.delete(f"/api/student/me/external-activities/{external_id}", headers={"X-Student-Id": "670510101"}).status_code == 204
    assert client.delete("/api/admin/students/670510102", headers={"X-Admin-Email": CENTRAL_ADMIN_EMAIL}).status_code == 200

    assert feed(client, CENTRAL_ADMIN_EMAIL)["notifications"] == []
    db_session.expire_all()
    assert db_session.query(AdminNotification).count() == 0


def test_notifications_require_admin(client):
    client.headers.pop("X-Admin-Email", None)
    assert client.get("/api/admin/notifications").status_code == 401


def add_admin_notifications(db_session, count, major=CS, created_at=None):
    for index in range(count):
        db_session.add(AdminNotification(
            type="external_submitted", major=major, student_id="670510101",
            student_name="สมชาย ใจดี", activity_title=f"Activity {index}",
            message="m", link="/admin/approvals",
            **({"created_at": created_at} if created_at else {}),
        ))
    db_session.commit()


def test_feed_is_paged_and_unread_count_covers_everything(client, db_session):
    add_admin_notifications(db_session, 45)

    first = feed(client, CS_ADMIN_EMAIL)
    assert len(first["notifications"]) == 30
    assert first["has_more"] is True
    assert first["unread_count"] == 45

    last_id = first["notifications"][-1]["id"]
    second = client.get("/api/admin/notifications", params={"before_id": last_id},
                        headers={"X-Admin-Email": CS_ADMIN_EMAIL}).json()
    assert len(second["notifications"]) == 15
    assert second["has_more"] is False
    assert all(item["id"] < last_id for item in second["notifications"])


def test_prune_removes_old_admin_notifications_and_their_read_rows(client, db_session):
    from models import AdminNotificationRead
    from notification_retention import prune_old_notifications

    add_admin_notifications(db_session, 3, created_at=datetime(2026, 1, 1, 9, 0))
    add_admin_notifications(db_session, 2)
    assert client.patch("/api/admin/notifications/read-all",
                        headers={"X-Admin-Email": CS_ADMIN_EMAIL}).json()["marked"] == 5

    result = prune_old_notifications(db_session, days=90, now=datetime(2026, 10, 5, 9, 0))

    assert result["admin"] == 3
    db_session.expire_all()
    assert db_session.query(AdminNotification).count() == 2
    assert db_session.query(AdminNotificationRead).count() == 2


def test_clear_all_hides_only_for_this_admin(client, db_session):
    from models import AdminNotificationRead

    add_admin_notifications(db_session, 3)
    cs = {"X-Admin-Email": CS_ADMIN_EMAIL}
    client.patch("/api/admin/notifications/read-all", headers=cs)

    assert client.delete("/api/admin/notifications", headers=cs).json() == {"cleared": 3}
    after = feed(client, CS_ADMIN_EMAIL)
    assert (after["notifications"], after["unread_count"]) == ([], 0)
    db_session.expire_all()
    assert db_session.query(AdminNotificationRead).count() == 0

    # แอดมินกลางยังเห็นครบ และแถวจริงยังอยู่
    assert len(feed(client, CENTRAL_ADMIN_EMAIL)["notifications"]) == 3
    assert db_session.query(AdminNotification).count() == 3

    # รายการใหม่หลังล้าง แสดงตามปกติ
    add_admin_notifications(db_session, 1)
    after_new = feed(client, CS_ADMIN_EMAIL)
    assert (len(after_new["notifications"]), after_new["unread_count"]) == (1, 1)
    assert client.delete("/api/admin/notifications", headers=cs).json() == {"cleared": 1}
    assert client.delete("/api/admin/notifications", headers=cs).json() == {"cleared": 0}
