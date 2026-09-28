from datetime import date

from models import ExternalActivity, Notification, Student, StudentRequest


def create_student(db_session, student_id="670510659") -> Student:
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


def create_external_activity(db_session, student_id="670510659") -> ExternalActivity:
    activity = ExternalActivity(
        student_id=student_id,
        title="Volunteer Camp",
        organization="Some NGO",
        activity_type="จิตอาสา / บริการสังคม",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 12),
        location="Chiang Mai",
        role="participant",
        description="",
        evidence_filename="evidence.png",
        evidence_original_name="evidence.png",
        evidence_content_type="image/png",
        evidence_size=100,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def test_demo_bypass_auto_creates_missing_student(client, db_session):
    # ไม่มี student '999999999' อยู่ในระบบเลย แต่ endpoint ที่ใช้
    # get_current_student ต้องไม่ 404 (bypass auth สำหรับเดโม)
    response = client.get(
        "/api/student/me/external-activities",
        headers={"X-Student-Id": "999999999"},
    )

    assert response.status_code == 200
    assert response.json() == {"total": 0, "external_activities": []}

    student = db_session.get(Student, "999999999")
    assert student is not None


def test_reject_external_activity_requires_reason_and_notifies_student(
    client,
    db_session,
):
    create_student(db_session)
    activity = create_external_activity(db_session)

    no_reason_response = client.patch(
        f"/api/external-activities/{activity.id}/decision",
        json={"status": "rejected"},
    )
    assert no_reason_response.status_code == 400

    response = client.patch(
        f"/api/external-activities/{activity.id}/decision",
        json={"status": "rejected", "reject_reason": "ไฟล์หลักฐานไม่ชัดเจน"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["reject_reason"] == "ไฟล์หลักฐานไม่ชัดเจน"

    notification = (
        db_session.query(Notification)
        .filter_by(student_id="670510659")
        .one_or_none()
    )
    assert notification is not None
    assert notification.source == "external_activity"
    assert notification.status == "Rejected"
    assert notification.message == "ไฟล์หลักฐานไม่ชัดเจน"
    assert notification.is_read is False


def test_reject_student_request_requires_reason_and_notifies_student(
    client,
    db_session,
):
    create_student(db_session)

    request = StudentRequest(
        requester_name="Test Student",
        requester_student_id="670510659",
        request_type="skill_validation",
        detail="ขอ validate ทักษะ",
        status="pending",
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)

    no_reason_response = client.patch(
        f"/api/requests/{request.id}",
        json={"status": "rejected"},
    )
    assert no_reason_response.status_code == 400

    response = client.patch(
        f"/api/requests/{request.id}",
        json={"status": "rejected", "reject_reason": "ข้อมูลไม่ครบถ้วน"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["reject_reason"] == "ข้อมูลไม่ครบถ้วน"

    notification = (
        db_session.query(Notification)
        .filter_by(student_id="670510659")
        .one_or_none()
    )
    assert notification is not None
    assert notification.source == "student_request"
    assert notification.status == "Rejected"
    assert notification.message == "ข้อมูลไม่ครบถ้วน"


def test_list_and_mark_notifications(client, db_session):
    create_student(db_session)
    activity = create_external_activity(db_session)

    client.patch(
        f"/api/external-activities/{activity.id}/decision",
        json={"status": "rejected", "reject_reason": "กรุณาแนบไฟล์ใหม่"},
    )

    list_response = client.get(
        "/api/student/me/notifications",
        headers={"X-Student-Id": "670510659"},
    )
    assert list_response.status_code == 200

    notifications = list_response.json()
    assert len(notifications) == 1
    assert notifications[0]["read"] is False
    assert notifications[0]["message"] == "กรุณาแนบไฟล์ใหม่"
    assert notifications[0]["activityId"] == activity.id

    mark_response = client.patch(
        "/api/student/me/notifications/mark-all-read",
        headers={"X-Student-Id": "670510659"},
    )
    assert mark_response.status_code == 200

    list_response_after = client.get(
        "/api/student/me/notifications",
        headers={"X-Student-Id": "670510659"},
    )
    assert list_response_after.json()[0]["read"] is True


def test_notifications_say_which_source_their_id_belongs_to(client, db_session):
    # id ของคำขอกิจกรรมภายนอกกับ id ของ student_request ชนกันได้
    # frontend ต้องรู้ว่า activityId มาจากไหนจึงจะเปิดถูกรายการ
    create_student(db_session)
    activity = create_external_activity(db_session)
    request = StudentRequest(
        requester_name="Test Student",
        requester_student_id="670510659",
        request_type="skill_validation",
        detail="ขอ validate ทักษะ",
        status="pending",
    )
    db_session.add(request)
    db_session.commit()

    client.patch(
        f"/api/external-activities/{activity.id}/decision",
        json={"status": "rejected", "reject_reason": "แนบไฟล์ใหม่"},
    )
    client.patch(
        f"/api/requests/{request.id}",
        json={"status": "rejected", "reject_reason": "ข้อมูลไม่ครบ"},
    )

    notifications = client.get(
        "/api/student/me/notifications",
        headers={"X-Student-Id": "670510659"},
    ).json()

    by_source = {item["source"]: item["activityId"] for item in notifications}
    assert by_source == {
        "external_activity": activity.id,
        "student_request": request.id,
    }
