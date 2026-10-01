"""ไฟล์หลักฐานต้องยืนยันตัวตนนักศึกษาด้วย get_current_student เหมือน endpoint อื่น

เดิม endpoint ไฟล์หลักฐานเทียบ header X-Student-Id เองตรง ๆ และไม่สน
X-Student-Email คู่ที่ get_current_student ปฏิเสธ (อีเมลคนหนึ่ง + รหัสอีกคน)
จึงยังเปิดไฟล์ได้ และตอนทำล็อกอินจริงถ้าแก้แค่ get_current_student endpoint นี้
จะยังเปิดด้วย header ปลอมได้ (ดู docs/security-review.md ข้อ ก6)
"""

import pytest

from models import Student
from tests.conftest import CENTRAL_ADMIN_EMAIL, CHEM_ADMIN_EMAIL
from tests.test_external_activity_evidence_files import PNG_BYTES, create_request

OWNER = "670510101"
ATTACKER = "670510102"


def create_student(db_session, student_id, email, major="วิทยาการคอมพิวเตอร์"):
    db_session.add(
        Student(
            student_id=student_id,
            first_name="Test",
            last_name=student_id,
            email=email,
            faculty="Faculty of Science",
            major=major,
        )
    )
    db_session.commit()


@pytest.fixture()
def evidence_urls(client, db_session, upload_dir):
    create_student(db_session, OWNER, "owner@cmu.ac.th")
    create_student(db_session, ATTACKER, "attacker@cmu.ac.th")
    activity = create_request(db_session, upload_dir, student_id=OWNER)
    # ทดสอบในฐานะนักศึกษา: เอา header แอดมินที่ client ตั้งไว้ออก
    client.headers.pop("X-Admin-Email", None)
    return [
        f"/api/external-activities/{activity.id}/evidence",
        f"/api/external-activities/{activity.id}/evidence/{activity.evidence_files[0].id}",
    ]


@pytest.mark.parametrize("index", [0, 1])
def test_attacker_email_with_owner_id_is_rejected(client, evidence_urls, index):
    response = client.get(
        evidence_urls[index],
        headers={"X-Student-Email": "attacker@cmu.ac.th", "X-Student-Id": OWNER},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("index", [0, 1])
def test_owner_session_can_open_file(client, evidence_urls, index):
    response = client.get(
        evidence_urls[index],
        headers={"X-Student-Email": "owner@cmu.ac.th", "X-Student-Id": OWNER},
    )

    assert response.status_code == 200
    assert response.content == PNG_BYTES


@pytest.mark.parametrize("index", [0, 1])
def test_other_student_cannot_open_file(client, evidence_urls, index):
    response = client.get(
        evidence_urls[index],
        headers={"X-Student-Email": "attacker@cmu.ac.th", "X-Student-Id": ATTACKER},
    )

    assert response.status_code == 403


@pytest.mark.parametrize("index", [0, 1])
def test_no_identity_is_rejected(client, evidence_urls, index):
    assert client.get(evidence_urls[index]).status_code == 401


def test_evidence_uses_the_shared_student_check(client, evidence_urls, monkeypatch):
    # จุดยืนยันตัวตนนักศึกษามีจุดเดียว: เปลี่ยน get_current_student แล้ว endpoint นี้เปลี่ยนตาม
    import main

    def reject_everyone(*args, **kwargs):
        raise main.HTTPException(status_code=401, detail="real login required")

    monkeypatch.setattr(main, "get_current_student", reject_everyone)

    response = client.get(evidence_urls[1], headers={"X-Student-Id": OWNER})

    assert response.status_code == 401


def test_admin_access_is_still_scoped_by_branch(client, evidence_urls):
    chem = client.get(evidence_urls[1], headers={"X-Admin-Email": CHEM_ADMIN_EMAIL})
    central = client.get(evidence_urls[1], headers={"X-Admin-Email": CENTRAL_ADMIN_EMAIL})

    assert chem.status_code == 403
    assert central.status_code == 200
