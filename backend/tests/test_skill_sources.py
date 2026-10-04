from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader
from models import Activity, ActivityMember, ActivitySkill, ExternalActivity, ExternalActivitySkill, Student
from transcript_data import collect_transcript
from transcript_pdf import render_transcript_pdf

SID = '690519901'
HEADERS = {'X-Student-Id': SID}


def add_internal(db, student, source, hours, level, status='completed'):
    activity = Activity(name=f'{source} activity', activity_type='Workshop',
        major=student.major if source == 'major' else None, activity_hours=hours,
        start_at=datetime(2026, 8, 1, 9), end_at=datetime(2026, 8, 1, 12),
        status=status, responsible_person='Admin', location='Campus',
        skill_levels=[ActivitySkill(skill_key='volunteerism', target_role='participant', level=level)])
    db.add(activity)
    db.flush()
    db.add(ActivityMember(student_id=student.student_id, activity_id=activity.id))
    db.commit()
    return activity


def add_external(db, student, hours, level, status):
    activity = ExternalActivity(student_id=student.student_id, title=f'{status} external',
        organization='External Org', activity_type='Workshop', start_date=date(2026, 8, 2),
        end_date=date(2026, 8, 2), role='participant', location='Campus', status=status,
        activity_hours=hours, skill_levels=[ExternalActivitySkill(skill_key='volunteerism',
            target_role='participant', level=level)])
    db.add(activity)
    db.commit()
    return activity


def seed(db):
    student = Student(student_id=SID, first_name='Source', last_name='Test',
        email='sources@test.local', major='Chemistry')
    db.add(student)
    db.commit()
    add_internal(db, student, 'major', 6, 2)
    add_internal(db, student, 'faculty', 4, 4)
    return student


def personal(client):
    return client.get('/api/student/me/skills', headers=HEADERS).json()


def admin(client):
    return client.get('/api/admin/student-skills?year=2026').json()


def test_three_source_example_and_admin_aggregate_invariance(client, db_session):
    student = seed(db_session)
    baseline = admin(client)
    before_personal = personal(client)
    add_external(db_session, student, 3, 5, 'approved')
    add_external(db_session, student, 10, 5, 'pending')
    add_external(db_session, student, 20, 1, 'rejected')
    body = personal(client)
    assert body['hours'] == {'major': 6, 'faculty': 4, 'external': 3, 'total': 13}
    period = body['periods']['year-2026']
    assert period['skillsBySource']['major']['volunteerism'] == 2
    assert period['skillsBySource']['faculty']['volunteerism'] == 4
    assert period['skillsBySource']['external']['volunteerism'] == 5
    assert period['comparisons']['external']['average'] is None
    assert period['comparisons']['major'] == before_personal['periods']['year-2026']['comparisons']['major']
    assert period['comparisons']['faculty'] == before_personal['periods']['year-2026']['comparisons']['faculty']
    report = admin(client)
    row, old = report['students'][0], baseline['students'][0]
    for key in ('skills', 'majorSkills', 'facultySkills', 'activityCount', 'skillActivityCounts', 'majorActivityAverage'):
        assert row[key] == old[key]
    for key in ('benchmarkScores', 'facultyActivityAverage', 'population'):
        assert report[key] == baseline[key]
    assert row['externalSkills'] == period['skillsBySource']['external']
    assert row['hours'] == body['hours']
    assert row['activityCounts'] == {'major': 1, 'faculty': 1, 'external': 1}
    assert row['activityCount'] == 2
    assert client.get('/api/student/me/activities', headers=HEADERS).json()['hours'] == body['hours']
    assert client.get('/api/student/me/transcript/options', headers=HEADERS).json()['hours'] == body['hours']


@pytest.mark.parametrize('status', [None, 'pending', 'rejected'])
def test_external_empty_does_not_create_zero_profiles(client, db_session, status):
    student = seed(db_session)
    if status:
        add_external(db_session, student, 10, 5, status)
    body = personal(client)
    external = body['periods']['year-2026']['comparisons']['external']
    assert all(value is None for value in external['skills'].values())
    assert external['average'] is None
    assert body['hours']['external'] == 0


def test_multiple_approved_decimal_hours_and_individual_only(client, db_session):
    student = seed(db_session)
    add_external(db_session, student, Decimal('1.25'), 5, 'approved')
    add_external(db_session, student, Decimal('2.50'), 3, 'approved')
    other = Student(student_id='690519902', first_name='Other', last_name='Student',
        email='other-source@test.local', major='Chemistry')
    db_session.add(other)
    db_session.commit()
    add_internal(db_session, other, 'major', 1, 4)
    body = personal(client)
    assert body['hours']['external'] == 3.75
    assert body['hours']['total'] == 13.75
    assert body['periods']['year-2026']['comparisons']['external']['skills']['volunteerism'] == 4
    report = {row['id']: row for row in admin(client)['students']}
    assert report[other.student_id]['skills']['volunteerism'] == 4
    assert report[other.student_id]['externalSkills']['volunteerism'] is None
    baseline_profile = body['periods']['year-2026']['comparisons']
    baseline_report = admin(client)
    add_external(db_session, other, 50, 1, 'approved')
    add_external(db_session, student, 20, 1, 'pending')
    add_external(db_session, student, 20, 1, 'rejected')
    after = personal(client)['periods']['year-2026']['comparisons']
    assert after == baseline_profile
    assert 'populationAverage' not in after['external']
    after_report = admin(client)
    assert 'externalActivityAverage' not in after_report
    for key in ('benchmarkScores', 'facultyActivityAverage', 'population'):
        assert after_report[key] == baseline_report[key]
    after_rows = {row['id']: row for row in after_report['students']}
    assert after_rows[SID]['externalSkills']['volunteerism'] == 4
    assert after_rows[other.student_id]['externalSkills']['volunteerism'] == 1


def test_transcript_source_hours_filters_and_real_pdfs(client, db_session):
    student = seed(db_session)
    add_external(db_session, student, 3, 5, 'approved')
    add_external(db_session, student, 10, 5, 'pending')
    data = collect_transcript(db_session, student)
    assert data['summary']['hours'] == {'major': 6, 'faculty': 4, 'external': 3, 'total': 13}
    assert {item['source'] for group in data['groups'] for item in group['activities']} == {'major', 'faculty', 'external'}
    for source, hours in [('major', 6), ('faculty', 4), ('external', 3)]:
        filtered = collect_transcript(db_session, student, scope=source)
        assert filtered['summary']['hours']['total'] == hours
        assert filtered['summary']['hours'][source] == hours
        exported = client.get(f'/api/student/me/skills/export?period=year-2026&source={source}', headers=HEADERS)
        assert exported.status_code == 200, exported.text
        assert exported.content.startswith(b'%PDF')
        text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(exported.content)).pages)
        assert f'Source: {source}' in text
        assert 'pending external' not in text
    for style in ('A', 'B'):
        pdf = render_transcript_pdf(data, style)
        assert pdf.startswith(b'%PDF')
        text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
        assert '13.0' in text and '6.0' in text and '4.0' in text and '3.0' in text


def test_hours_exclude_cancelled_future_and_other_major(client, db_session):
    student = seed(db_session)
    add_internal(db_session, student, 'major', 10, 5, 'cancelled')
    future = add_internal(db_session, student, 'faculty', 20, 5, 'active')
    future.end_at = datetime(2090, 8, 1)
    other = add_internal(db_session, student, 'major', 30, 5)
    other.major = 'Physics'
    db_session.commit()
    assert personal(client)['hours'] == {'major': 6, 'faculty': 4, 'external': 0, 'total': 10}


def test_external_only_student_can_be_viewed_but_is_not_evaluated_internally(client, db_session):
    student = Student(student_id=SID, first_name='External', last_name='Only', email='only@test.local', major='Chemistry')
    db_session.add(student)
    db_session.commit()
    add_external(db_session, student, 3, 5, 'approved')
    row = admin(client)['students'][0]
    assert row['activityCount'] == 0
    assert all(value is None for value in row['skills'].values())
    assert row['externalSkills']['volunteerism'] == 5
