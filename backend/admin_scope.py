"""กรองข้อมูลฝั่ง admin ตามสาขาของนักศึกษา (students.major)

- แอดมินกลาง (major=None) เห็นทุกสาขา รวมนักศึกษาที่ไม่มีสาขา
- แอดมินสาขาเห็นเฉพาะนักศึกษาที่ major ตรงกับสาขาตัวเอง
  นักศึกษาที่ไม่มีสาขา (หรือคำขอที่หานักศึกษาไม่เจอ) จึงเห็นได้เฉพาะแอดมินกลาง
"""

from fastapi import HTTPException
from sqlalchemy import func, or_

from admin_auth import AdminContext
from major_utils import normalize_major
from models import Activity, ExternalActivity, Student, StudentRequest


OTHER_MAJOR_DETAIL = "ไม่มีสิทธิ์เข้าถึงข้อมูลของนักศึกษานอกสาขาที่ดูแล"
OTHER_ACTIVITY_MAJOR_DETAIL = "ไม่มีสิทธิ์เข้าถึงกิจกรรมนอกสาขาที่ดูแล"


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


def activity_major_condition(admin: AdminContext, include_unowned: bool = True):
    """เงื่อนไข filter บน Activity (None = ไม่ต้องกรอง)

    include_unowned=True (ค่าเริ่มต้น): กิจกรรมที่ major เป็น None (สร้างโดย
    แอดมินกลาง หรือกิจกรรมเก่าก่อนมีคอลัมน์นี้) ให้ทุกแอดมินเห็นได้ ใช้กับ
    หน้ารายการ/รายละเอียดกิจกรรมที่แอดมินสาขาควรเห็นกิจกรรมที่ยังไม่มีเจ้าของด้วย

    include_unowned=False: นับเฉพาะกิจกรรมที่เป็นของสาขาตัวเองจริง ๆ ใช้กับ
    สถิติ Dashboard ที่ไม่ควรเอากิจกรรมที่ยังไม่มีเจ้าของมานับเป็นของสาขาไหน

    หมายเหตุ: เทียบ Activity.major ตรงตัวและใช้ IS NULL เป็นกิจกรรมส่วนกลาง
    ถูกต้องได้เพราะพึ่งการ normalize ตอนบันทึก (Activity._normalize_major ใน
    models.py: ตัดช่องว่าง ค่าว่าง = NULL) และ admin.major ก็ normalize แล้ว
    (admin_auth.list_bypass_admins) ถ้าเขียน major โดยไม่ผ่าน ORM ต้อง normalize เอง
    """
    if admin.is_central:
        return None

    if include_unowned:
        return or_(
            Activity.major == admin.major,
            Activity.major.is_(None),
        )

    return Activity.major == admin.major


def scope_activity_query(query, admin: AdminContext, include_unowned: bool = True):
    condition = activity_major_condition(admin, include_unowned=include_unowned)
    return query if condition is None else query.filter(condition)


def can_access_activity(admin: AdminContext, activity: Activity | None) -> bool:
    if admin.is_central:
        return True

    if activity is None:
        return False

    return activity.major is None or activity.major == admin.major


def ensure_can_access_activity(admin: AdminContext, activity: Activity | None) -> None:
    if not can_access_activity(admin, activity):
        raise HTTPException(
            status_code=403,
            detail=OTHER_ACTIVITY_MAJOR_DETAIL,
        )


def resolve_branch_filter(admin: AdminContext, major: str | None) -> AdminContext:
    """แอดมินกลางเลือก filter สาขา (query param ?major=) ได้จากหน้า Dashboard/
    Activities/Student Skills/Approvals -- คืน AdminContext จำลองเป็นแอดมิน
    สาขานั้นแทน เพื่อให้ scope_*_query/ensure_can_access_* เดิมใช้ได้ตรง ๆ
    โดยไม่ต้องเขียนเงื่อนไข major ซ้ำทุก endpoint

    แอดมินสาขาเรียกมาเองอยู่แล้วถูก scope ตามสาขาตัวเองอยู่แล้ว จึงไม่รับผลจาก
    query param นี้ (กันแอดมินสาขาสวมรอยดูสาขาอื่นผ่าน query param)
    """
    if not admin.is_central:
        return admin

    selected = normalize_major(major)

    if selected is None:
        return admin

    return AdminContext(email=admin.email, name=admin.name, major=selected)
