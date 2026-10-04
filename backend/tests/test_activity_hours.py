from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
import json
from pypdf import PdfReader
from sqlalchemy.exc import IntegrityError

from activity_hours import total_activity_hours
from models import Activity, ActivityMember, ExternalActivity, Student
from transcript_data import collect_transcript
from transcript_pdf import render_transcript_pdf
from tests.test_external_activity_resubmit import PNG_BYTES

SID = '690519999'
HEADERS = {'X-Student-Id': SID}


def student(db):
    row = Student(student_id=SID, first_name='Hours', last_name='Test', email='hours@test.local')
    db.add(row)
    db.commit()
    return row


def payload(hours):
    return dict(name='Hours activity', activity_type='Workshop', activity_hours=hours,
                start_at='2090-01-01T09:00:00', end_at='2090-01-01T12:00:00',
                responsible_person='Admin', location='Campus')


def test_completed_pending_edit_cancel_duplicate_and_skills(client, db_session):
    student(db_session)
    a = client.post('/api/activities', json={**payload(6), 'participant_skills': {'volunteerism': 3}}).json()
    b = client.post('/api/activities', json=payload(3)).json()
    db_session.add_all([ActivityMember(activity_id=a['id'], student_id=SID),
                        ActivityMember(activity_id=b['id'], student_id=SID)])
    db_session.commit()
    assert client.patch(f"/api/activities/{a['id']}", json={'status': 'completed'}).status_code == 200
    response = client.get('/api/student/me/activities', headers=HEADERS).json()
    assert response['total_activity_hours'] == 6
    assert sorted(x['activity_hours'] for x in response['activities']) == [3, 6]
    before = client.get('/api/student/me/skills', headers=HEADERS).json()
    assert client.patch(f"/api/activities/{b['id']}", json={'status': 'completed'}).status_code == 200
    assert client.get('/api/student/me/activities', headers=HEADERS).json()['total_activity_hours'] == 9
    assert client.patch(f"/api/activities/{a['id']}", json={'activity_hours': 1.5}).json()['activity_hours'] == 1.5
    after = client.get('/api/student/me/skills', headers=HEADERS).json()
    assert {key: period['skills'] for key, period in before['periods'].items()} == {
        key: period['skills'] for key, period in after['periods'].items()
    }
    assert after['total_activity_hours'] == 4.5
    # The membership composite key prevents duplicate participation.
    db_session.add(ActivityMember(activity_id=a['id'], student_id=SID))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert total_activity_hours(db_session, SID) == Decimal('4.5')
    client.patch(f"/api/activities/{b['id']}", json={'status': 'cancelled'})
    assert client.get('/api/student/me/activities', headers=HEADERS).json()['total_activity_hours'] == 1.5


@pytest.mark.parametrize('hours', [-1, 0, 'NaN', 'Infinity', 1.234, 100000000])
def test_invalid_create_hours(client, hours):
    assert client.post('/api/activities', json=payload(hours)).status_code == 422


@pytest.mark.parametrize('hours', [-1, None, 1.234, 'Infinity'])
def test_invalid_edit_hours(client, hours):
    activity = client.post('/api/activities', json=payload(6)).json()
    assert client.patch(f"/api/activities/{activity['id']}", json={'activity_hours': hours}).status_code in (400, 422)
    assert client.get(f"/api/activities/{activity['id']}").json()['activity_hours'] == 6


def test_external_statuses_elapsed_activity_and_pdf(client, db_session):
    row = student(db_session)
    now = datetime.now()
    activity = Activity(name='Elapsed', activity_type='Workshop', start_at=now-timedelta(days=2),
                        end_at=now-timedelta(days=1), responsible_person='Admin', location='Campus',
                        activity_hours=Decimal('1.25'))
    db_session.add(activity)
    db_session.flush()
    db_session.add(ActivityMember(activity_id=activity.id, student_id=SID))
    for status, hours in [('pending', 3), ('rejected', 7), ('approved', 2.5)]:
        db_session.add(ExternalActivity(student_id=SID, title=status, organization='Org',
            activity_type='Workshop', start_date=date.today(), end_date=date.today(),
            location='Campus', role='participant', status=status, activity_hours=hours))
    db_session.commit()
    assert total_activity_hours(db_session, SID) == Decimal('3.75')
    data = collect_transcript(db_session, row)
    assert data['summary']['total_activity_hours'] == 3.75
    assert collect_transcript(db_session, row, scope='external')['summary']['total_activity_hours'] == 2.5
    assert client.get('/api/student/me/transcript/options', headers=HEADERS).json()['total_activity_hours'] == 3.75
    for style in ('A', 'B'):
        pdf = render_transcript_pdf(data, style)
        assert pdf.startswith(b'%PDF')
        text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
        assert '3.75' in text and '2.5' in text


def test_old_clients_and_legacy_zero_hours(client):
    body = payload(6)
    del body['activity_hours']
    activity = client.post('/api/activities', json=body).json()
    assert activity['activity_hours'] == 0
    assert client.patch(f"/api/activities/{activity['id']}", json={'activity_hours': 0}).status_code == 200


def test_external_submission_approval_and_resubmission_hours(client, db_session):
    student(db_session)
    form = dict(title='External hours', organization='Org', activity_type='Workshop',
                start_date='2026-10-01', end_date='2026-10-01', location='Campus',
                role='participant', skills=json.dumps({'volunteerism': 3}), activity_hours='3.5')
    submitted = client.post('/api/student/me/external-activities', headers=HEADERS,
        data=form, files={'evidence': ('hours.png', PNG_BYTES, 'image/png')})
    assert submitted.status_code == 201, submitted.text
    activity = submitted.json()
    assert activity['activity_hours'] == 3.5
    assert total_activity_hours(db_session, SID) == 0
    decision_url = f"/api/external-activities/{activity['id']}/decision"
    rejected = client.patch(decision_url, json={'status': 'rejected', 'reject_reason': 'Please revise'})
    assert rejected.status_code == 200, rejected.text
    assert total_activity_hours(db_session, SID) == 0
    resubmitted = client.put(f"/api/student/me/external-activities/{activity['id']}",
        headers=HEADERS, data={**form, 'activity_hours': '2.25'})
    assert resubmitted.status_code == 200, resubmitted.text
    assert resubmitted.json()['activity_hours'] == 2.25
    assert total_activity_hours(db_session, SID) == 0
    approved = client.patch(decision_url, json={'status': 'approved'})
    assert approved.status_code == 200, approved.text
    db_session.expire_all()
    assert total_activity_hours(db_session, SID) == Decimal('2.25')


@pytest.mark.parametrize('hours', ['-1', '0', 'NaN', '1.234'])
def test_external_invalid_hours(client, db_session, hours):
    student(db_session)
    response = client.post('/api/student/me/external-activities', headers=HEADERS,
        data=dict(title='Invalid', organization='Org', activity_type='Workshop',
                  start_date='2026-10-01', end_date='2026-10-01', location='Campus',
                  role='participant', skills='{}', activity_hours=hours),
        files={'evidence': ('hours.png', PNG_BYTES, 'image/png')})
    assert response.status_code == 422
