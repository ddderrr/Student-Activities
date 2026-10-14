"""สาขาของนักศึกษา ณ วันที่ทำกิจกรรม (รองรับการย้ายสาขา)

กติกา:
- ประวัติของนักศึกษาไม่เปลี่ยนเมื่อย้ายสาขา: กิจกรรมของสาขาเดิมที่ทำตอนยังอยู่สาขาเดิม
  ยังเป็น "major" เหมือนเดิม กราฟทักษะ ชั่วโมง และ transcript จึงไม่เปลี่ยน
- ค่าเฉลี่ยสาขาก็นับตามสาขา ณ วันที่ทำกิจกรรม ค่าเฉลี่ยในอดีตจึงไม่เปลี่ยนเมื่อมีคนย้ายออก
- สิ่งที่เปลี่ยนมีอย่างเดียว: ตอน "เทียบสาขา" นักศึกษาถูกเทียบกับค่าเฉลี่ยของสาขาปัจจุบัน

ทุกจุดที่ตัดสิน activity_source ของกิจกรรมที่ผ่านมาแล้ว ต้องใช้ major_at() แทน student.major
"""

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy.orm import Session

from major_utils import normalize_major
from models import Student, StudentMajorHistory
from timeutil import now_bangkok

# [(ended_at, major), ...] เรียงจากเก่าไปใหม่
History = list[tuple[datetime, str]]


def load_major_histories(db: Session, student_ids: Iterable[str]) -> dict[str, History]:
    ids = list(set(student_ids))
    if not ids:
        return {}

    histories: dict[str, History] = {}
    rows = (
        db.query(StudentMajorHistory.student_id, StudentMajorHistory.ended_at, StudentMajorHistory.major)
        .filter(StudentMajorHistory.student_id.in_(ids))
        .order_by(StudentMajorHistory.ended_at, StudentMajorHistory.id)
        .all()
    )
    for student_id, ended_at, major in rows:
        histories.setdefault(student_id, []).append((ended_at, major))
    return histories


def major_at(current_major: str | None, history: History | None, when: datetime | None) -> str | None:
    """สาขาของนักศึกษา ณ เวลา when (ไม่มีประวัติ / ไม่รู้เวลา = สาขาปัจจุบัน)"""
    if when is not None:
        for ended_at, major in history or ():
            if when < ended_at:
                return major
    return normalize_major(current_major)


def change_student_major(db: Session, student: Student, new_major: str | None, now: datetime | None = None) -> bool:
    """เปลี่ยนสาขาปัจจุบัน และบันทึกสาขาเดิมไว้ในประวัติ คืน True ถ้าสาขาเปลี่ยนจริง

    นักศึกษาที่ยังไม่มีสาขาแล้วได้สาขาครั้งแรก ถือเป็นการกรอกข้อมูลที่ขาด ไม่ใช่การย้าย
    จึงไม่บันทึกประวัติ (กิจกรรมเก่าจะนับตามสาขาใหม่)
    """
    old = normalize_major(student.major)
    new = normalize_major(new_major)
    if old == new:
        return False

    if old:
        db.add(StudentMajorHistory(student_id=student.student_id, major=old, ended_at=now or now_bangkok()))
    student.major = new or ""
    return True
