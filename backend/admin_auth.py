"""ระบุตัวแอดมินที่เรียก API ฝั่ง admin (ที่เดียวในระบบ)

1. Authorization: Bearer <token> จาก POST /api/auth/login (หน้า /login)
   ตรวจกับตาราง admins ทุกครั้ง: แอดมินที่ถูกลบแล้วใช้ token เดิมต่อไม่ได้
2. โหมด bypass สำหรับพัฒนา/เทสต์: header X-Admin-Email (ต้องตั้ง
   ADMIN_BYPASS_ENABLED=true) หาจากตาราง admins ก่อน แล้วจึง admin_accounts.py

endpoint อื่นใช้แค่ AdminContext ไม่ต้องรู้ว่ามาจากทางไหน
"""

import os
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

import admin_accounts
from auth_tokens import bearer_token, read_token
from database import get_db
from major_utils import normalize_major
from models import Admin


BYPASS_DISABLED_DETAIL = (
    "โหมดทดสอบแอดมิน (bypass) ยังไม่ได้เปิด: "
    "เพิ่ม ADMIN_BYPASS_ENABLED=true ใน .env แล้วรีสตาร์ท backend"
)


@dataclass(frozen=True)
class AdminContext:
    email: str
    name: str
    # None = แอดมินกลางของคณะ เห็นทุกสาขา
    major: str | None
    # id ในตาราง admins (None = บัญชี bypass จาก admin_accounts.py)
    id: int | None = None

    @property
    def is_central(self) -> bool:
        return self.major is None


def is_admin_bypass_enabled() -> bool:
    # อ่านทุกครั้งที่เรียก ไม่ cache เพื่อให้เปลี่ยนค่าใน .env/เทสต์แล้วมีผลทันที
    value = os.getenv("ADMIN_BYPASS_ENABLED", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def list_bypass_admins() -> list[AdminContext]:
    return [
        AdminContext(
            email=account["email"].strip().lower(),
            name=account.get("name") or account["email"],
            major=normalize_major(account.get("major")),
        )
        for account in admin_accounts.ADMIN_ACCOUNTS
    ]


def find_bypass_admin(email: str | None) -> AdminContext | None:
    normalized = (email or "").strip().lower()

    if not normalized:
        return None

    return next(
        (admin for admin in list_bypass_admins() if admin.email == normalized),
        None,
    )


def admin_context(admin: Admin) -> AdminContext:
    return AdminContext(
        email=admin.email,
        name=admin.full_name or admin.email,
        major=admin.major,
        id=admin.id,
    )


def admin_from_token(token: str | None, db: Session) -> AdminContext | None:
    subject = read_token(token, "admin")

    if not subject or not subject.isdigit():
        return None

    admin = db.get(Admin, int(subject))
    return admin_context(admin) if admin else None


def admin_from_bypass_header(email: str | None, db: Session) -> AdminContext | None:
    normalized = (email or "").strip().lower()

    if not normalized or not is_admin_bypass_enabled():
        return None

    admin = db.query(Admin).filter(Admin.email == normalized).first()
    return admin_context(admin) if admin else find_bypass_admin(normalized)


def get_optional_admin(
    authorization: str | None = Header(default=None),
    x_admin_email: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AdminContext | None:
    # ใช้กับ endpoint ที่ทั้งแอดมินและนักศึกษาเรียกได้ (เช่น ไฟล์หลักฐาน)
    return (
        admin_from_token(bearer_token(authorization), db)
        or admin_from_bypass_header(x_admin_email, db)
    )


def get_current_admin(
    authorization: str | None = Header(default=None),
    x_admin_email: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AdminContext:
    token = bearer_token(authorization)

    if token:
        admin = admin_from_token(token, db)

        if admin is None:
            raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบใหม่")

        return admin

    if not is_admin_bypass_enabled():
        # ส่ง header bypass มาแต่ปิดไว้: บอกวิธีเปิดให้นักพัฒนา
        detail = BYPASS_DISABLED_DETAIL if x_admin_email else "กรุณาเข้าสู่ระบบ"
        raise HTTPException(status_code=401, detail=detail)

    admin = admin_from_bypass_header(x_admin_email, db)

    if admin is None:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")

    return admin


def require_central_admin(
    admin: AdminContext = Depends(get_current_admin),
) -> AdminContext:
    if not admin.is_central:
        raise HTTPException(
            status_code=403,
            detail="เฉพาะแอดมินกลางของคณะเท่านั้น",
        )

    return admin
