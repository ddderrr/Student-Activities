from datetime import datetime

import pytest

from skill_definitions import PARTICIPANT_SKILL_DEFINITIONS as DEFINITIONS
from skill_scoring import source_skill_details, population_skill_average
from models import ActivitySkill, Student
from tests.test_skill_sources import add_internal, add_external, seed, personal, admin, SID


def item(key, hours, skills, source='faculty'):
    return {'key': key, 'scope': source, 'activity_hours': hours, 'skills': skills}


def test_exact_faculty_null_example_and_duplicate_protection():
    first = item('f1', 3, {'academics': 2, 'volunteerism': 2})
    second = item('f2', 3, {'academics': 2, 'volunteerism': None})
    profile = source_skill_details([first, second, first], DEFINITIONS)['faculty']
    assert profile['source_activity_hours'] == 6
    assert profile['skills']['academics'] == {'level': 2, 'exposure_hours': 6, 'activity_count': 2}
    assert profile['skills']['volunteerism'] == {'level': 2, 'exposure_hours': 3, 'activity_count': 1}
    assert profile['skills']['health_promotion'] == {'level': None, 'exposure_hours': 0, 'activity_count': 0}


def test_hours_weighting_keeps_full_precision():
    profile = source_skill_details([
        item('f1', 3, {'academics': 2}), item('f2', 6, {'academics': 4})
    ], DEFINITIONS)['faculty']
    assert profile['skills']['academics'] == {'level': 10 / 3, 'exposure_hours': 9, 'activity_count': 2}


def test_zero_hours_do_not_invent_a_weighted_score():
    profile = source_skill_details([item('legacy', 0, {'academics': 5})], DEFINITIONS)['faculty']
    assert profile['skills']['academics'] == {'level': None, 'exposure_hours': 0, 'activity_count': 1}


@pytest.mark.parametrize('hours', [(20, 2), (2, 20)])
def test_population_equal_student_weight_and_null_denominator(hours):
    profiles = [source_skill_details([item('a', hours[0], {'academics': 2, 'volunteerism': 2})], DEFINITIONS)['faculty'],
                source_skill_details([item('b', hours[1], {'academics': 4})], DEFINITIONS)['faculty'],
                source_skill_details([item('c', 7, {'academics': 3, 'volunteerism': 4})], DEFINITIONS)['faculty']]
    averages = population_skill_average(profiles, DEFINITIONS)
    assert averages['academics'] == {'average': 3, 'sample_count': 3}
    assert averages['volunteerism'] == {'average': 3, 'sample_count': 2}
    assert averages['health_promotion'] == {'average': None, 'sample_count': 0}


@pytest.mark.parametrize('changed_source', ['major', 'faculty', 'external'])
def test_each_source_is_independent(changed_source):
    activities = [item(source, 2, {'academics': 2}, source) for source in ('major', 'faculty', 'external')]
    before = source_skill_details(activities, DEFINITIONS)
    activities[next(i for i, a in enumerate(activities) if a['scope'] == changed_source)]['skills']['academics'] = 5
    after = source_skill_details(activities, DEFINITIONS)
    for source in before:
        if source != changed_source:
            assert after[source] == before[source]


def test_student_admin_api_exact_example_and_total_hours(client, db_session):
    student = Student(student_id=SID, first_name='Weighted', last_name='Student', email='weighted@test.local', major='Chemistry')
    db_session.add(student)
    db_session.commit()
    f1 = add_internal(db_session, student, 'faculty', 3, 2)
    f2 = add_internal(db_session, student, 'faculty', 3, 2)
    f2.skill_levels.clear()  # Missing Volunteerism is the database representation of NULL.
    for activity in (f1, f2):
        activity.skill_levels.append(ActivitySkill(skill_key='academics', target_role='participant', level=2))
    db_session.commit()
    add_internal(db_session, student, 'major', 2, 5)
    add_external(db_session, student, 4, 4, 'approved')
    add_external(db_session, student, 100, 1, 'pending')
    add_external(db_session, student, 100, 1, 'rejected')
    body = personal(client)
    period = body['periods']['year-2026']
    assert body['hours'] == period['hours'] == {'major': 2, 'faculty': 6, 'external': 4, 'total': 12}
    profile = period['sourceProfiles']['faculty']
    assert profile['skills']['academics'] == {'level': 2, 'exposure_hours': 6, 'activity_count': 2}
    assert profile['skills']['volunteerism'] == {'level': 2, 'exposure_hours': 3, 'activity_count': 1}
    row = admin(client)['students'][0]
    assert row['sourceProfiles'] == period['sourceProfiles']
    assert row['hours'] == body['hours']
    assert len(row['activitiesBySource']['external']) == 1
    assert period['comparisons']['external']['average'] is None
    assert 'externalActivityAverage' not in admin(client)


def test_period_completion_population_precision_and_major_membership(client, db_session):
    student = seed(db_session)
    f1 = add_internal(db_session, student, 'faculty', 3, 2)
    f2 = add_internal(db_session, student, 'faculty', 6, 4)
    future = add_internal(db_session, student, 'faculty', 100, 5, 'active')
    future.end_at = datetime(2090, 8, 1)
    cancelled = add_internal(db_session, student, 'faculty', 100, 5, 'cancelled')
    for activity in (f1, f2, future, cancelled):
        activity.skill_levels.append(ActivitySkill(skill_key='academics', target_role='participant', level=activity.skill_levels[0].level))
    f1.start_at = datetime(2026, 2, 1)
    f2.start_at = datetime(2026, 3, 1)
    other = Student(student_id='690519902', first_name='Other', last_name='Student', email='weighted-other@test.local', major='Physics')
    db_session.add(other)
    db_session.commit()
    other_f = add_internal(db_session, other, 'faculty', 2, 4)
    other_f.start_at = datetime(2026, 3, 1)
    other_f.skill_levels.append(ActivitySkill(skill_key='academics', target_role='participant', level=4))
    add_internal(db_session, other, 'major', 100, 1)
    db_session.commit()
    period = personal(client)['periods']['semester-1-2026']
    assert period['sourceProfiles']['faculty']['skills']['academics']['level'] == pytest.approx(10 / 3)
    assert period['comparisons']['faculty']['average']['academics'] == pytest.approx(11 / 3)
    assert period['comparisons']['faculty']['sampleCounts']['academics'] == 2
    assert period['hours'] == {'major': 0, 'faculty': 9, 'external': 0, 'total': 9}
    second_semester = personal(client)['periods']['semester-2-2026']
    assert second_semester['comparisons']['major']['average']['volunteerism'] == 2
    assert second_semester['sourceProfiles']['faculty']['skills']['academics']['level'] is None


def test_admin_cohort_aggregates_use_source_profiles(client, db_session):
    student = seed(db_session)
    other = Student(student_id='680519902', first_name='Other', last_name='Year', email='cohort-weighted@test.local', major='Chemistry')
    db_session.add(other)
    db_session.commit()
    add_internal(db_session, other, 'faculty', 2, 2)
    report = admin(client)
    aggregate = report['populationProfiles']['["680519902","690519901"]']
    assert aggregate['faculty']['skills']['volunteerism'] == 3
    assert aggregate['faculty']['sampleCounts']['volunteerism'] == 2
    assert report['populationProfiles']['["690519901"]']['major']['skills']['volunteerism'] == 2
    assert 'external' not in aggregate


def test_real_source_hours_include_unevaluated_activities_without_fake_skill_data(client, db_session):
    student = seed(db_session)
    unevaluated = add_internal(db_session, student, 'faculty', 7, 3)
    unevaluated.skill_levels.clear()
    unevaluated.start_at = datetime(2025, 3, 1)
    db_session.commit()
    body = personal(client)
    profile = body['periods']['year-2025']['sourceProfiles']['faculty']
    assert profile['source_activity_hours'] == 7
    assert body['periods']['year-2025']['hours']['faculty'] == 7
    assert profile['skills']['academics'] == {'level': None, 'exposure_hours': 0, 'activity_count': 0}
    assert profile['skills']['volunteerism'] == {'level': None, 'exposure_hours': 0, 'activity_count': 0}
