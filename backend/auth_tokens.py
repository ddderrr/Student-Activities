"""รหัสผ่านแอดมิน (PBKDF2) และ token ของ session หลัง login (HMAC-SHA256)

token = base64url(payload JSON) + "." + base64url(HMAC(payload))
payload: {"role": "admin" | "student", "sub": admin id / student_id, "exp": unix time}

ตั้ง AUTH_SECRET ใน .env (ต้องเปลี่ยนก่อนใช้งานจริง) ถ้าไม่ตั้งจะใช้ค่า dev
ที่ใครก็รู้ ทำให้ปลอม token ได้
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

TOKEN_TTL_SECONDS = 24 * 60 * 60
PASSWORD_ITERATIONS = 200_000
DEV_SECRET = "dev-insecure-secret-change-me"


def _secret() -> bytes:
    return (os.getenv("AUTH_SECRET") or DEV_SECRET).encode()


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
    payload = json.dumps(
        {"role": role, "sub": str(subject), "exp": int(time.time()) + TOKEN_TTL_SECONDS},
        separators=(",", ":"),
    ).encode()
    signature = hmac.new(_secret(), payload, hashlib.sha256).digest()
    return f"{_b64encode(payload)}.{_b64encode(signature)}"


def read_token(token: str | None, role: str) -> str | None:
    """คืน subject ถ้า token ถูกต้อง ยังไม่หมดอายุ และเป็น role ที่ต้องการ ไม่งั้น None"""
    try:
        payload_part, signature_part = (token or "").split(".")
        payload = _b64decode(payload_part)
        expected = hmac.new(_secret(), payload, hashlib.sha256).digest()
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
