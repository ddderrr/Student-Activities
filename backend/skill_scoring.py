"""กติกากลางของการนับกิจกรรมและคะแนนทักษะ

ใช้ร่วมกันทั้ง My Skills, Transcript PDF, Student Skills (admin) และ Dashboard
แก้กติกาที่นี่ที่เดียว ห้ามเขียนเงื่อนไข status ซ้ำในแต่ละ query
"""

from collections.abc import Iterable, Mapping
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, or_

from major_utils import normalize_major
from models import Activity, ExternalActivity
from timeutil import now_bangkok

SOURCES = ('major', 'faculty', 'external')


def completed_activity_filter(now_value=None):
    """Use the existing earned-hours completion rule for personal skill evidence."""
    return (Activity.status != 'cancelled') & or_(
        Activity.status == 'completed', Activity.end_at < (now_value or now_bangkok())
    )


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
            if skill_key in values and level is not None:
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


def source_skill_profiles(activities, definitions):
    """Compatibility score maps backed by the detailed weighted profiles."""
    return {
        source: {key: detail['level'] for key, detail in profile['skills'].items()}
        for source, profile in source_skill_details(activities, definitions).items()
    }


def calculate_source_profile(activities, definitions, source):
    """One student, one source; callers supply eligible, period/role-filtered evidence.

    Deduplicate activities before summing. A missing skill is not an observation.
    Zero-hour legacy evidence has no weighted level; its assessed activity still
    counts, and no hours or score are invented.
    """
    unique = {}
    for index, activity in enumerate(activities):
        if activity.get('scope', activity.get('source')) != source:
            continue
        identity = activity.get('key') or (activity.get('source'), activity.get('id', index))
        unique.setdefault(identity, activity)
    details = {}
    for key in definitions:
        numerator = Decimal(0)
        exposure = Decimal(0)
        count = 0
        for activity in unique.values():
            score = activity.get('skills', {}).get(key)
            if score is None:
                continue
            hours = Decimal(str(activity.get('earned_activity_hours', activity.get('activity_hours', 0)) or 0))
            count += 1
            exposure += hours
            numerator += Decimal(str(score)) * hours
        details[key] = {
            'level': float(numerator / exposure) if exposure > 0 else None,
            'exposure_hours': float(exposure),
            'activity_count': count,
        }
    total = sum((Decimal(str(a.get('earned_activity_hours', a.get('activity_hours', 0)) or 0))
                 for a in unique.values()), Decimal(0))
    return {'source': source, 'source_activity_hours': float(total), 'skills': details}


def source_skill_details(activities, definitions):
    activities = list(activities)
    return {source: calculate_source_profile(activities, definitions, source) for source in SOURCES}


def population_skill_average(profiles, definitions):
    """Average final personal levels equally, with a separate denominator per skill."""
    profiles = list(profiles)
    result = {}
    for key in definitions:
        values = [profile['skills'][key]['level'] for profile in profiles
                  if profile['skills'][key]['level'] is not None]
        result[key] = {'average': sum(values) / len(values) if values else None,
                       'sample_count': len(values)}
    return result


def profile_summary(profile):
    values = {key: detail['level'] for key, detail in profile['skills'].items()
              if detail['level'] is not None}
    return {'score': sum(values.values()) / len(values) if values else None,
            'primarySkill': max(values, key=values.get) if values else None}


def cohort_population_profiles(students, definitions):
    """Precompute current cohort/group combinations so Vue only selects API results."""
    import json

    def year_group(level):
        return 'UNKNOWN' if level is None else '5+' if level >= 5 else str(level)

    years = {year_group(student['yearLevel']) for student in students}
    majors = {student['major'] for student in students}
    result = {}
    for year in [None, *sorted(years)]:
        for major in [None, *sorted(majors)]:
            cohort = [s for s in students if (year is None or year_group(s['yearLevel']) == year)
                      and (major is None or s['major'] == major)]
            key = json.dumps(sorted(s['id'] for s in cohort), separators=(',', ':'), ensure_ascii=False)
            result[key] = {}
            for source in ('major', 'faculty'):
                averages = population_skill_average([s['sourceProfiles'][source] for s in cohort], definitions)
                valid = [s['sourceSummaries'][source]['score'] for s in cohort
                         if s['sourceSummaries'][source]['score'] is not None]
                result[key][source] = {
                    'skills': {k: v['average'] for k, v in averages.items()},
                    'sampleCounts': {k: v['sample_count'] for k, v in averages.items()},
                    'score': sum(valid) / len(valid) if valid else None,
                    'evaluatedCount': len(valid),
                }
    return result


def round_half_up(value: float, ndigits: int = 0) -> float | int:
    """ปัดเศษครึ่งขึ้นจากค่าจริงของ float (เหมือน JavaScript Math.round / toFixed)

    ต่างจาก round() ของ Python ที่ปัดครึ่งไปหาเลขคู่ เช่น round(62.5) = 62 แต่ตรงนี้ = 63
    ใช้กับตัวเลขที่ต้องตรงกับที่หน้าเว็บเคยคำนวณเอง (กราฟ Skill Distribution)
    """
    quantum = Decimal(1).scaleb(-ndigits)
    rounded = Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP)
    return int(rounded) if ndigits == 0 else float(rounded)
