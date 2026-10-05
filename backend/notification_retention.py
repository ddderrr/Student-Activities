"""ล้างการแจ้งเตือนเก่า (รันตอนเปิด backend) กันตาราง notification โตไม่สิ้นสุด

- นักศึกษา: ลบเฉพาะที่อ่านแล้ว และเก่ากว่า NOTIFICATION_RETENTION_DAYS (ที่ยังไม่อ่านเก็บไว้เสมอ)
- แอดมิน: สถานะอ่านแยกตามแอดมินแต่ละคน จึงลบตามอายุอย่างเดียว พร้อมแถวสถานะอ่านของรายการนั้น
  (คำขอที่ยังค้างดูได้ครบที่หน้าการอนุมัติอยู่แล้ว)
ตั้ง NOTIFICATION_RETENTION_DAYS=0 เพื่อปิดการล้าง
"""

import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import AdminNotification, AdminNotificationRead, Notification
from timeutil import now_bangkok

DEFAULT_RETENTION_DAYS = 90


def retention_days() -> int:
    try:
        return max(0, int(os.getenv("NOTIFICATION_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)))
    except ValueError:
        return DEFAULT_RETENTION_DAYS


def prune_old_notifications(db: Session, days: int | None = None, now: datetime | None = None) -> dict[str, int]:
    days = retention_days() if days is None else days
    if days <= 0:
        return {"student": 0, "admin": 0}

    cutoff = (now or now_bangkok()) - timedelta(days=days)

    student = (
        db.query(Notification)
        .filter(Notification.is_read.is_(True), Notification.created_at < cutoff)
        .delete(synchronize_session=False)
    )

    old_admin_ids = db.query(AdminNotification.id).filter(AdminNotification.created_at < cutoff)
    db.query(AdminNotificationRead).filter(
        AdminNotificationRead.notification_id.in_(old_admin_ids.scalar_subquery())
    ).delete(synchronize_session=False)
    admin = (
        db.query(AdminNotification)
        .filter(AdminNotification.created_at < cutoff)
        .delete(synchronize_session=False)
    )

    db.commit()
    return {"student": student, "admin": admin}
