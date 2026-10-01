"""token ต้องเซ็นด้วย AUTH_SECRET ที่ตั้งเองเท่านั้น (fail closed)

เดิมถ้าไม่ได้ตั้ง AUTH_SECRET ระบบใช้ค่า dev ที่เขียนไว้ในโค้ด (อยู่ใน git)
ใครก็สร้าง token แอดมินกลางเองได้ แม้ปิด ADMIN_BYPASS_ENABLED
"""

import base64
import hashlib
import hmac
import json
import logging
import time

import pytest

from auth_tokens import hash_password, issue_token
from models import Admin, Student

OLD_DEV_SECRET = b"dev-insecure-secret-change-me"
SHORT_SECRET = "x" * 31


def sign(role, subject, secret: bytes) -> str:
    def b64(raw):
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    payload = json.dumps(
        {"role": role, "sub": str(subject), "exp": int(time.time()) + 3600},
        separators=(",", ":"),
    ).encode()
    return f"{b64(payload)}.{b64(hmac.new(secret, payload, hashlib.sha256).digest())}"


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def accounts(client, db_session, monkeypatch):
    # จำลองเครื่องจริง: ปิด bypass และไม่ส่ง header แอดมิน
    monkeypatch.setenv("ADMIN_BYPASS_ENABLED", "false")
    client.headers.pop("X-Admin-Email", None)
    db_session.add(
        Admin(
            email="central@gmail.com",
            first_name="แอดมินกลาง",
            last_name="คณะวิทยาศาสตร์",
            major=None,
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


def login(client, email):
    return client.post("/api/auth/login", json={"email": email, "password": "1234"})


@pytest.mark.parametrize("secret", [None, "", SHORT_SECRET])
def test_token_signed_with_old_dev_secret_is_rejected(accounts, monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("AUTH_SECRET", raising=False)
    else:
        monkeypatch.setenv("AUTH_SECRET", secret)

    admin = accounts.get("/api/admin/me", headers=bearer(sign("admin", 1, OLD_DEV_SECRET)))
    student = accounts.get("/api/student/me", headers=bearer(sign("student", "670510001", OLD_DEV_SECRET)))

    assert admin.status_code == 401
    assert student.status_code == 401


@pytest.mark.parametrize("secret", [None, "", SHORT_SECRET])
@pytest.mark.parametrize("email", ["central@gmail.com", "student@cmu.ac.th"])
def test_login_without_valid_secret_issues_no_token(accounts, monkeypatch, secret, email):
    if secret is None:
        monkeypatch.delenv("AUTH_SECRET", raising=False)
    else:
        monkeypatch.setenv("AUTH_SECRET", secret)

    response = login(accounts, email)

    assert response.status_code == 503
    assert "token" not in response.json()
    assert "AUTH_SECRET" in response.json()["detail"]


def test_token_signed_with_short_secret_is_rejected(accounts, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", SHORT_SECRET)

    response = accounts.get("/api/admin/me", headers=bearer(sign("admin", 1, SHORT_SECRET.encode())))

    assert response.status_code == 401


def test_login_and_token_work_with_configured_secret(accounts):
    # conftest ตั้ง AUTH_SECRET แบบสุ่มให้ทุกเทสต์
    response = login(accounts, "central@gmail.com")
    assert response.status_code == 200, response.text
    assert accounts.get("/api/admin/me", headers=bearer(response.json()["token"])).status_code == 200

    # นักศึกษาจริง login ด้วยรหัสร่วมไม่ได้ (ดู test_student_mock_login.py) ออก token ให้ตรง ๆ
    token = issue_token("student", "670510001")
    assert accounts.get("/api/student/me", headers=bearer(token)).status_code == 200


def test_token_signed_with_another_secret_is_rejected(accounts):
    other = b"another-secret-that-is-long-enough-123456"

    response = accounts.get("/api/admin/me", headers=bearer(sign("admin", 1, other)))

    assert response.status_code == 401


@pytest.mark.parametrize("secret", [None, SHORT_SECRET])
def test_startup_warns_when_secret_missing_or_short(monkeypatch, caplog, secret):
    from auth_tokens import warn_if_auth_secret_missing

    if secret is None:
        monkeypatch.delenv("AUTH_SECRET", raising=False)
    else:
        monkeypatch.setenv("AUTH_SECRET", secret)

    with caplog.at_level(logging.WARNING):
        warn_if_auth_secret_missing()

    assert "AUTH_SECRET" in caplog.text


def test_startup_is_quiet_when_secret_configured(caplog):
    from auth_tokens import warn_if_auth_secret_missing

    with caplog.at_level(logging.WARNING):
        warn_if_auth_secret_missing()

    assert "AUTH_SECRET" not in caplog.text
