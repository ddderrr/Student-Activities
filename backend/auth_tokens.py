"""รหัสผ่านแอดมิน (PBKDF2) และ token ของ session หลัง login (HMAC-SHA256)

token = base64url(payload JSON) + "." + base64url(HMAC(payload))
payload: {"role": "admin" | "student", "sub": admin id / student_id, "exp": unix time}

ต้องตั้ง AUTH_SECRET ใน .env (อย่างน้อย MIN_SECRET_LENGTH ตัวอักษร) ถ้าไม่ได้ตั้งหรือสั้นเกิน
ระบบจะไม่ออกและไม่รับ token เลย (fail closed) ไม่มีค่าสำรองในโค้ด เพราะค่าที่อยู่ใน git
ใครก็ใช้ปลอม token ได้ สร้างค่าสุ่มด้วย:

    python -c "import secrets; print(secrets.token_urlsafe(48))"
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time

TOKEN_TTL_SECONDS = 24 * 60 * 60
PASSWORD_ITERATIONS = 200_000
MIN_SECRET_LENGTH = 32

logger = logging.getLogger("uvicorn.error")


class AuthNotConfigured(RuntimeError):
    """ยังไม่ได้ตั้ง AUTH_SECRET (หรือสั้นเกิน): ออก token ไม่ได้"""


def _secret() -> bytes | None:
    # อ่านทุกครั้ง ไม่ cache (เปลี่ยนใน .env / เทสต์แล้วมีผลทันที) ค่าสั้นเกิน = ไม่ได้ตั้ง
    value = (os.getenv("AUTH_SECRET") or "").strip()
    return value.encode() if len(value) >= MIN_SECRET_LENGTH else None


def is_auth_configured() -> bool:
    return _secret() is not None


def warn_if_auth_secret_missing() -> None:
    """เรียกตอน backend เริ่ม: บอกชัด ๆ ว่าทำไม login ไม่ได้"""
    if not is_auth_configured():
        logger.warning(
            "AUTH_SECRET is not set or shorter than %d characters: login is disabled "
            "and every token is rejected. Generate one with "
            "python -c \"import secrets; print(secrets.token_urlsafe(48))\" "
            "and put it in .env, then restart the backend.",
            MIN_SECRET_LENGTH,
        )


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), _b64decode(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, _b64decode(expected))


def issue_token(role: str, subject: str) -> str:
    secret = _secret()

    if secret is None:
        raise AuthNotConfigured

    payload = json.dumps(
        {"role": role, "sub": str(subject), "exp": int(time.time()) + TOKEN_TTL_SECONDS},
        separators=(",", ":"),
    ).encode()
    signature = hmac.new(secret, payload, hashlib.sha256).digest()
    return f"{_b64encode(payload)}.{_b64encode(signature)}"


def read_token(token: str | None, role: str) -> str | None:
    """คืน subject ถ้า token ถูกต้อง ยังไม่หมดอายุ และเป็น role ที่ต้องการ ไม่งั้น None"""
    secret = _secret()

    if secret is None:
        return None

    try:
        payload_part, signature_part = (token or "").split(".")
        payload = _b64decode(payload_part)
        expected = hmac.new(secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature_part)):
            return None
        data = json.loads(payload)
    except (ValueError, TypeError):
        return None

    if data.get("role") != role or int(data.get("exp", 0)) < time.time():
        return None
    return str(data.get("sub") or "") or None


def bearer_token(authorization: str | None) -> str | None:
    scheme, _, value = (authorization or "").partition(" ")
    return value.strip() if scheme.lower() == "bearer" and value.strip() else None
