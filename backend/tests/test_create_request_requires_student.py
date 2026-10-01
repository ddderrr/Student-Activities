"""POST /api/requests ต้องยืนยันตัวตนนักศึกษา และใช้ตัวตนนั้นเป็นผู้ขอ

เดิมไม่ตรวจตัวตนเลย และเชื่อ requester_student_id / requester_name จาก body
ใครก็สร้างคำขอในนามนักศึกษาคนอื่นได้ (ดู docs/security-review.md ข้อ ก3)
"""

from models import Student, StudentRequest

STUDENT_ID = "670510001"


def create_student(db_session, student_id=STUDENT_ID, first_name="สมชาย"):
    db_session.add(
        Student(
            student_id=student_id,
            first_name=first_name,
            last_name="ใจดี",
            email=f"{student_id}@cmu.ac.th",
            faculty="Faculty of Science",
            major="เคมี",
        )
    )
    db_session.commit()


def post_request(client, headers=None, **body):
    payload = {"request_type": "skill_validation", "detail": "ขอตรวจทักษะ", **body}
    return client.post("/api/requests", json=payload, headers=headers or {})


def test_create_request_without_student_identity_is_rejected(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_BYPASS_ENABLED", "false")
    create_student(db_session)

    response = post_request(
        client,
        requester_student_id=STUDENT_ID,
        requester_name="สมชาย ใจดี",
    )

    assert response.status_code == 401
    assert db_session.query(StudentRequest).count() == 0


def test_requester_comes_from_authenticated_student_not_body(client, db_session):
    create_student(db_session, "670510001", "ผู้ขอจริง")
    create_student(db_session, "670510002", "เหยื่อ")

    response = post_request(
        client,
        headers={"X-Student-Id": "670510001"},
        requester_student_id="670510002",
        requester_name="เหยื่อ ใจดี",
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["requester_student_id"] == "670510001"
    assert body["requester_name"] == "ผู้ขอจริง ใจดี"
    request = db_session.query(StudentRequest).one()
    assert request.requester_student_id == "670510001"


def test_student_can_create_request_without_requester_fields(client, db_session):
    create_student(db_session)

    response = post_request(client, headers={"X-Student-Id": STUDENT_ID})

    assert response.status_code == 201, response.text
    assert response.json()["requester_student_id"] == STUDENT_ID
    assert response.json()["status"] == "pending"


def test_invalid_request_type_is_still_rejected(client, db_session):
    create_student(db_session)

    response = post_request(client, headers={"X-Student-Id": STUDENT_ID}, request_type="other")

    assert response.status_code == 400
