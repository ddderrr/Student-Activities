"""กติกากลางของการนับกิจกรรมและคะแนนทักษะ

ใช้ร่วมกันทั้ง My Skills, Transcript PDF, Student Skills (admin) และ Dashboard
แก้กติกาที่นี่ที่เดียว ห้ามเขียนเงื่อนไข status ซ้ำในแต่ละ query
"""

from collections.abc import Iterable, Mapping

from models import Activity, ExternalActivity


def counted_activity_filter():
    """กิจกรรมของคณะที่นับ: ทุกสถานะยกเว้นที่ถูกยกเลิก (cancelled)"""
    return Activity.status != "cancelled"


def counted_external_activity_filter():
    """กิจกรรมภายนอกที่นับ: เฉพาะที่แอดมินอนุมัติแล้ว"""
    return ExternalActivity.status == "approved"


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
