"""กรองข้อมูลฝั่ง admin ตามสาขาของนักศึกษา (students.major)

- แอดมินกลาง (major=None) เห็นทุกสาขา รวมนักศึกษาที่ไม่มีสาขา
- แอดมินสาขาเห็นเฉพาะนักศึกษาที่ major ตรงกับสาขาตัวเอง
  นักศึกษาที่ไม่มีสาขา (หรือคำขอที่หานักศึกษาไม่เจอ) จึงเห็นได้เฉพาะแอดมินกลาง
"""

from fastapi import HTTPException
from sqlalchemy import func

from admin_auth import AdminContext
from models import ExternalActivity, Student, StudentRequest


OTHER_MAJOR_DETAIL = "ไม่มีสิทธิ์เข้าถึงข้อมูลของนักศึกษานอกสาขาที่ดูแล"


def student_major_condition(admin: AdminContext):
    """เงื่อนไข filter บน Student สำหรับ query ที่ join Student แล้ว (None = ไม่ต้องกรอง)"""
    if admin.is_central:
        return None

    return func.trim(Student.major) == admin.major


def scope_student_query(query, admin: AdminContext):
    condition = student_major_condition(admin)
    return query if condition is None else query.filter(condition)


def scope_external_activity_query(query, admin: AdminContext):
    if admin.is_central:
        return query

    return scope_student_query(
        query.join(Student, Student.student_id == ExternalActivity.student_id),
        admin,
    )


def scope_student_request_query(query, admin: AdminContext):
    # inner join: คำขอที่หานักศึกษาไม่เจอ (ไม่มีสาขา) จึงไม่โผล่ให้แอดมินสาขา
    if admin.is_central:
        return query

    return scope_student_query(
        query.join(Student, Student.student_id == StudentRequest.requester_student_id),
        admin,
    )


def can_access_student(admin: AdminContext, student: Student | None) -> bool:
    if admin.is_central:
        return True

    if student is None:
        return False

    return (student.major or "").strip() == admin.major


def ensure_can_access_student(admin: AdminContext, student: Student | None) -> None:
    if not can_access_student(admin, student):
        raise HTTPException(status_code=403, detail=OTHER_MAJOR_DETAIL)


def ensure_can_assign_major(admin: AdminContext, major: str) -> None:
    # แอดมินสาขาย้ายนักศึกษาไปสาขาอื่นไม่ได้ (ไม่อย่างนั้นจะหลุดออกจาก scope ตัวเอง)
    if not admin.is_central and (major or "").strip() != admin.major:
        raise HTTPException(
            status_code=403,
            detail="แอดมินสาขาเปลี่ยนสาขาของนักศึกษาเป็นสาขาอื่นไม่ได้",
        )
