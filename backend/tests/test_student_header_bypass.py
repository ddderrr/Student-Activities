"""header X-Student-Id / X-Student-Email ใช้ได้เฉพาะตอนเปิด ADMIN_BYPASS_ENABLED

ปิด bypass (ค่าเริ่มต้น) แล้วต้องใช้ Bearer token จาก POST /api/auth/login เท่านั้น
เดิมส่ง X-Student-Id ของใครก็เป็นคนนั้นได้ทันที และไม่มีสวิตช์ปิด
(ดู docs/security-review.md ข้อ ข1, ข2)
"""

import pytest

from auth_tokens import issue_token
from models import Student
from tests.test_external_activity_evidence_files import create_request

STUDENT_ID = "670510001"


@pytest.fixture()
def bypass_off(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_BYPASS_ENABLED", "false")
    client.headers.pop("X-Admin-Email", None)
    db_session.add(
        Student(
            student_id=STUDENT_ID,
            first_name="สมชาย",
            last_name="ใจดี",
            email="student@cmu.ac.th",
            faculty="Faculty of Science",
            major="เคมี",
        )
    )
    db_session.commit()
    return client


@pytest.mark.parametrize(
    "headers",
    [
        {"X-Student-Id": STUDENT_ID},
        {"X-Student-Email": "student@cmu.ac.th"},
        {"X-Student-Email": "student@cmu.ac.th", "X-Student-Id": STUDENT_ID},
    ],
)
def test_student_headers_rejected_when_bypass_off(bypass_off, headers):
    response = bypass_off.get("/api/student/me", headers=headers)

    assert response.status_code == 401


def test_unknown_student_id_header_does_not_create_student_when_bypass_off(bypass_off, db_session):
    response = bypass_off.get("/api/student/me", headers={"X-Student-Id": "999999999"})

    assert response.status_code == 401
    assert db_session.get(Student, "999999999") is None


def test_evidence_rejects_student_header_when_bypass_off(bypass_off, db_session, upload_dir):
    activity = create_request(db_session, upload_dir, student_id=STUDENT_ID)

    response = bypass_off.get(
        f"/api/external-activities/{activity.id}/evidence/{activity.evidence_files[0].id}",
        headers={"X-Student-Id": STUDENT_ID},
    )

    assert response.status_code == 401


def test_bearer_token_still_works_when_bypass_off(bypass_off):
    token = issue_token("student", STUDENT_ID)

    response = bypass_off.get("/api/student/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["student_id"] == STUDENT_ID


def test_student_header_still_works_when_bypass_on(client, db_session):
    # conftest เปิด bypass ไว้ (เทสต์และเครื่องมือพัฒนาใช้ header ได้ต่อ)
    db_session.add(
        Student(
            student_id=STUDENT_ID,
            first_name="สมชาย",
            last_name="ใจดี",
            email="student@cmu.ac.th",
            faculty="Faculty of Science",
            major="เคมี",
        )
    )
    db_session.commit()

    response = client.get("/api/student/me", headers={"X-Student-Id": STUDENT_ID})

    assert response.status_code == 200
