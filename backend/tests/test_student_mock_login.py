"""นักศึกษา login ด้วยรหัสร่วม 1234 ได้เฉพาะตอนเปิด bypass

ปิด ADMIN_BYPASS_ENABLED แล้วทางลัด dev ปิดหมด นักศึกษา login ไม่ได้เลย (แอดมิน
login ด้วยรหัสผ่านจริงได้ตามปกติ) เปิดแล้วนักศึกษาทุกคนในตาราง students login
ด้วยอีเมลของตัวเองได้ ระหว่างที่ยังไม่มี CMU IT Account SSO (ดู
docs/security-review.md ข้อ ข5) ระยะยาวจะทำ CMU OAuth
"""

import pytest

from auth_tokens import hash_password
from models import Admin, Student
from student_bypass import STUDENT_LOGIN_ACCOUNTS, STUDENT_MOCK_PASSWORD

INVALID_DETAIL = "อีเมลหรือรหัสผ่านไม่ถูกต้อง"
REAL_STUDENT_EMAIL = "real.student@cmu.ac.th"


@pytest.fixture()
def accounts(client, db_session):
    client.headers.pop("X-Admin-Email", None)
    for email, student_id in STUDENT_LOGIN_ACCOUNTS.items():
        db_session.add(
            Student(
                student_id=student_id,
                first_name="ทดสอบ",
                last_name=student_id,
                email=email,
                faculty="Faculty of Science",
                major="เคมี",
            )
        )
    # นักศึกษาจริงที่ import จากหน้า Settings
    db_session.add(
        Student(
            student_id="670510500",
            first_name="นักศึกษา",
            last_name="จริง",
            email=REAL_STUDENT_EMAIL,
            faculty="Faculty of Science",
            major="เคมี",
        )
    )
    db_session.add(
        Admin(
            email="central@gmail.com",
            first_name="แอดมินกลาง",
            last_name="คณะวิทยาศาสตร์",
            major=None,
            password_hash=hash_password("admin-real-password"),
        )
    )
    db_session.commit()
    return client


def login(client, email, password=STUDENT_MOCK_PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.mark.parametrize("email", [*STUDENT_LOGIN_ACCOUNTS, REAL_STUDENT_EMAIL])
def test_bypass_off_no_student_can_login_with_shared_password(accounts, monkeypatch, email):
    monkeypatch.setenv("ADMIN_BYPASS_ENABLED", "false")

    response = login(accounts, email)

    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_DETAIL}


def test_bypass_off_admin_still_logs_in_with_real_password(accounts, monkeypatch):
    monkeypatch.setenv("ADMIN_BYPASS_ENABLED", "false")

    response = login(accounts, "central@gmail.com", "admin-real-password")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.parametrize("email, student_id", list(STUDENT_LOGIN_ACCOUNTS.items()))
def test_bypass_on_test_accounts_can_login(accounts, email, student_id):
    # conftest เปิด ADMIN_BYPASS_ENABLED ไว้
    response = login(accounts, email)

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "student"
    assert response.json()["student"]["student_id"] == student_id


def test_bypass_on_imported_student_logs_in_with_own_email(accounts):
    # ยังไม่มี SSO: นักศึกษาที่ import จากหน้า Settings login ด้วยอีเมลตัวเอง + รหัสร่วมได้
    response = login(accounts, f"  {REAL_STUDENT_EMAIL.upper()} ")

    assert response.status_code == 200
    assert response.json()["role"] == "student"
    assert response.json()["student"]["student_id"] == "670510500"


def test_bypass_on_imported_student_with_wrong_password_is_rejected(accounts):
    response = login(accounts, REAL_STUDENT_EMAIL, "0000")

    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_DETAIL}


def test_bypass_on_test_account_with_wrong_password_is_rejected(accounts):
    response = login(accounts, next(iter(STUDENT_LOGIN_ACCOUNTS)), "0000")

    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_DETAIL}
