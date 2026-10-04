"""Participation hours, independent of skill scores and without stored totals."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, or_
from models import Activity, ActivityMember, ExternalActivity, Student
from skill_scoring import activity_source


def effective_completed(activity, now_value):
    if activity.status == "cancelled":
        return False
    if activity.status == "completed":
        return True
    return activity.end_at is not None and activity.end_at < now_value


def earned_internal_hours(activity, now_value=None):
    if not effective_completed(activity, now_value or datetime.now()):
        return Decimal(0)
    return activity.activity_hours or Decimal(0)


def hours_summary_from_items(items):
    totals = {source: Decimal(0) for source in ('major', 'faculty', 'external')}
    for item in items:
        source = item['source']
        if source in totals:
            totals[source] += Decimal(str(item.get('earned_activity_hours', 0)))
    return {**{source: float(value) for source, value in totals.items()},
            'total': float(sum(totals.values(), Decimal(0)))}


def activity_hours_summary(db, student):
    return activity_hours_summaries(db, [student])[student.student_id]


def activity_hours_summaries(db, students):
    # Composite membership key prevents duplicates; hours are independent of skill tracks.
    by_id = {student.student_id: student for student in students}
    items = {student_id: [] for student_id in by_id}
    if not by_id:
        return {}
    internal = db.query(ActivityMember.student_id, Activity.major, func.sum(Activity.activity_hours)).join(
        ActivityMember, ActivityMember.activity_id == Activity.id
    ).filter(ActivityMember.student_id.in_(by_id), Activity.status != "cancelled",
             or_(Activity.status == "completed", Activity.end_at < datetime.now()))
    internal = internal.group_by(ActivityMember.student_id, Activity.major).all()
    external = db.query(ExternalActivity.student_id, func.sum(ExternalActivity.activity_hours)).filter(
        ExternalActivity.student_id.in_(by_id), ExternalActivity.status == "approved"
    ).group_by(ExternalActivity.student_id).all()
    for student_id, major, hours in internal:
        items[student_id].append({'source': activity_source(major, by_id[student_id].major), 'earned_activity_hours': hours})
    for student_id, hours in external:
        items[student_id].append({'source': 'external', 'earned_activity_hours': hours})
    return {student_id: hours_summary_from_items(values) for student_id, values in items.items()}


def total_activity_hours(db, student_id):
    student = db.get(Student, student_id)
    return Decimal(str(activity_hours_summary(db, student)['total'])) if student else Decimal(0)
