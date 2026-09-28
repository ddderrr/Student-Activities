"""ระบุตัวแอดมินที่เรียก API ฝั่ง admin (ที่เดียวในระบบ)

ตอนนี้ยังไม่มีระบบ login จริง: ใช้โหมด bypass สำหรับพัฒนา/ทดสอบ โดย frontend
ส่งอีเมลแอดมินจำลองมาใน header X-Admin-Email และต้องตั้ง
ADMIN_BYPASS_ENABLED=true ใน .env ไว้ ถ้าไม่ได้เปิด ทุก endpoint ฝั่ง admin
จะตอบ 401

เมื่อมีระบบ login จริง ให้แก้แค่ get_current_admin() ให้อ่านจาก session/token
แล้วคืน AdminContext เหมือนเดิม endpoint อื่นไม่ต้องเปลี่ยน
"""

import os
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

import admin_accounts


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
            major=(account.get("major") or "").strip() or None,
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


def get_optional_admin(
    x_admin_email: str | None = Header(default=None),
) -> AdminContext | None:
    # ใช้กับ endpoint ที่ทั้งแอดมินและนักศึกษาเรียกได้ (เช่น ไฟล์หลักฐาน)
    if not x_admin_email or not is_admin_bypass_enabled():
        return None

    return find_bypass_admin(x_admin_email)


def get_current_admin(
    x_admin_email: str | None = Header(default=None),
) -> AdminContext:
    if not is_admin_bypass_enabled():
        raise HTTPException(status_code=401, detail=BYPASS_DISABLED_DETAIL)

    admin = find_bypass_admin(x_admin_email)

    if admin is None:
        raise HTTPException(
            status_code=401,
            detail="ไม่พบแอดมิน (X-Admin-Email) กรุณาเลือกอีเมลที่หน้า login ใหม่",
        )

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
