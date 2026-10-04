"""กติกากลางของการนับกิจกรรมและคะแนนทักษะ

ใช้ร่วมกันทั้ง My Skills, Transcript PDF, Student Skills (admin) และ Dashboard
แก้กติกาที่นี่ที่เดียว ห้ามเขียนเงื่อนไข status ซ้ำในแต่ละ query
"""

from collections.abc import Iterable, Mapping
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, or_

from major_utils import normalize_major
from models import Activity, ExternalActivity


def counted_activity_filter():
    """กิจกรรมของคณะที่นับ: ทุกสถานะยกเว้นที่ถูกยกเลิก (cancelled)"""
    return Activity.status != "cancelled"


def counted_external_activity_filter():
    """กิจกรรมภายนอกที่นับ: เฉพาะที่แอดมินอนุมัติแล้ว"""
    return ExternalActivity.status == "approved"


def activity_source(activity_major: str | None, student_major: str | None) -> str:
    """ประเภทของกิจกรรมของคณะเมื่อมองจากนักศึกษาคนหนึ่ง

    faculty     = กิจกรรมส่วนกลางของคณะ (ไม่มีสาขาเจ้าของ หรือเป็นค่าว่าง)
    major       = กิจกรรมของสาขาเดียวกับนักศึกษา
    other_major = กิจกรรมของสาขาอื่น
    เทียบหลังตัดช่องว่างหน้า-หลัง
    """
    owner = normalize_major(activity_major)

    if owner is None:
        return "faculty"

    student = normalize_major(student_major)
    return "major" if student and owner == student else "other_major"


def faculty_activity_filter():
    """SQL คู่กับ activity_source(...) == "faculty" """
    return or_(Activity.major.is_(None), func.trim(Activity.major) == "")


def major_activity_filter(major: str):
    """SQL คู่กับ activity_source(...) == "major" ของนักศึกษาสาขา major"""
    return func.trim(Activity.major) == (major or "").strip()


def skill_levels_from_activities(
    activities: Iterable[Mapping],
    definitions: Mapping[str, str],
) -> dict[str, list[float]]:
    """รวม level ของแต่ละทักษะจากรายการกิจกรรม (แต่ละรายการมี "skills": {skill_key: level})

    ทักษะที่ไม่อยู่ใน definitions ไม่นับ
    """
    values: dict[str, list[float]] = {skill_key: [] for skill_key in definitions}

    for activity in activities:
        for skill_key, level in activity["skills"].items():
            if skill_key in values:
                values[skill_key].append(float(level))

    return values


def average_skill_levels(
    levels_by_skill: Mapping[str, list[float]],
    ndigits: int | None = 2,
) -> dict[str, float | None]:
    """ค่าเฉลี่ยของแต่ละทักษะ (ไม่มีคะแนน = None)

    ndigits=None: ไม่ปัดเศษ ใช้กับชั้นแรกของค่าเฉลี่ยแบบ student-first
    (เฉลี่ยรายนักศึกษาก่อน แล้วค่อยเฉลี่ยข้ามนักศึกษาและปัดเศษ)
    """
    averages: dict[str, float | None] = {}

    for skill_key, levels in levels_by_skill.items():
        if not levels:
            averages[skill_key] = None
            continue

        value = sum(levels) / len(levels)
        averages[skill_key] = value if ndigits is None else round(value, ndigits)

    return averages


def average_activity_skills(
    activities: Iterable[Mapping],
    definitions: Mapping[str, str],
) -> dict[str, float | None]:
    """ค่าเฉลี่ยทักษะจากรายการกิจกรรม ปัดเศษ 2 ตำแหน่ง"""
    return average_skill_levels(skill_levels_from_activities(activities, definitions))


def source_skill_profiles(activities, definitions):
    """Personal source profiles; external never has a population comparison."""
    return {
        source: average_activity_skills(
            [activity for activity in activities if activity['scope'] == source], definitions
        )
        for source in ('major', 'faculty', 'external')
    }


def student_first_average(
    levels_by_student: Mapping[str, Mapping[str, list[float]]],
    definitions: Mapping[str, str],
) -> dict[str, float | None]:
    """ค่าเฉลี่ยแบบ student-first: เฉลี่ยรายนักศึกษา (ไม่ปัดเศษ) แล้วเฉลี่ยข้ามนักศึกษา ปัดเศษ 2 ตำแหน่ง

    กันไม่ให้นักศึกษาที่มีกิจกรรมเยอะมีน้ำหนักมากกว่าคนอื่น
    """
    per_skill: dict[str, list[float]] = {skill_key: [] for skill_key in definitions}

    for student_levels in levels_by_student.values():
        for skill_key, value in average_skill_levels(student_levels, ndigits=None).items():
            if value is not None:
                per_skill[skill_key].append(value)

    return average_skill_levels(per_skill)


def round_half_up(value: float, ndigits: int = 0) -> float | int:
    """ปัดเศษครึ่งขึ้นจากค่าจริงของ float (เหมือน JavaScript Math.round / toFixed)

    ต่างจาก round() ของ Python ที่ปัดครึ่งไปหาเลขคู่ เช่น round(62.5) = 62 แต่ตรงนี้ = 63
    ใช้กับตัวเลขที่ต้องตรงกับที่หน้าเว็บเคยคำนวณเอง (กราฟ Skill Distribution)
    """
    quantum = Decimal(1).scaleb(-ndigits)
    rounded = Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP)
    return int(rounded) if ndigits == 0 else float(rounded)
