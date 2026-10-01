"""หน้า login ต้องไม่บอกว่าอีเมลไหนมีในระบบ

"ไม่พบบัญชี" กับ "รหัสผ่านผิด" ตอบเหมือนกัน (401 ข้อความเดียวกัน) และใช้เวลาเท่ากัน:
แอดมินตรวจรหัสผ่านแบบ PBKDF2 (ช้า) ทุกกรณีจึงต้องตรวจรหัสผ่านหนึ่งครั้งเหมือนกัน
ไม่งั้นดูจากเวลาที่ตอบก็รู้ว่าอีเมลไหนเป็นแอดมิน (ดู docs/security-review.md ข้อ ก12)
"""

import pytest

import main
from auth_tokens import hash_password
from models import Admin, Student

INVALID_DETAIL = "อีเมลหรือรหัสผ่านไม่ถูกต้อง"


@pytest.fixture()
def accounts(client, db_session):
    client.headers.pop("X-Admin-Email", None)
    db_session.add(
        Admin(
            email="cs@gmail.com",
            first_name="แอดมินสาขา",
            last_name="วิทยาการคอมพิวเตอร์",
            major="วิทยาการคอมพิวเตอร์",
            password_hash=hash_password("1234"),
        )
    )
    db_session.add(
        Student(
            student_id="670510001",
            first_name="สมชาย",
            last_name="ใจดี",
            email="student@cmu.ac.th",
            faculty="Faculty of Science",
            major="เคมี",
        )
    )
    db_session.commit()
    return client


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.mark.parametrize(
    "email, password",
    [
        ("nobody@gmail.com", "1234"),
        ("cs@gmail.com", "0000"),
        ("student@cmu.ac.th", "0000"),
    ],
)
def test_unknown_email_and_wrong_password_look_the_same(accounts, email, password):
    response = login(accounts, email, password)

    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_DETAIL}


@pytest.mark.parametrize(
    "email, password",
    [
        ("nobody@gmail.com", "1234"),
        ("cs@gmail.com", "0000"),
        ("cs@gmail.com", "1234"),
        ("student@cmu.ac.th", "0000"),
        ("student@cmu.ac.th", "1234"),
    ],
)
def test_every_login_checks_a_password_hash_once(accounts, monkeypatch, email, password):
    calls = []
    real_verify = main.verify_password

    def counting_verify(*args):
        calls.append(args)
        return real_verify(*args)

    monkeypatch.setattr(main, "verify_password", counting_verify)

    login(accounts, email, password)

    assert len(calls) == 1
