"""เวลาทั้งระบบเป็นเวลาไทย (Asia/Bangkok) ไม่ขึ้นกับ timezone ของเครื่องที่รัน backend (B28)

ก่อนแก้: submitted_at มาจาก DB now() (session UTC) แต่ decided_at มาจาก datetime.now()
ของเครื่อง (+07) ส่งวันที่ 4 ต.ค. ตอนเช้าจึงแสดงเป็น 3 ต.ค.
"""

import base64
import json
import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from models import ExternalActivity, Student
from timeutil import BANGKOK, now_bangkok, today_bangkok

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
STUDENT_ID = "670510101"


@pytest.fixture()
def host_in_utc():
    # จำลอง backend ที่รันบนเครื่อง / container ที่ตั้งเป็น UTC
    original = os.environ.get("TZ")
    os.environ["TZ"] = "UTC"
    time.tzset()
    yield
    if original is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = original
    time.tzset()


def bangkok_now_from_utc():
    return datetime.now(timezone.utc).astimezone(BANGKOK).replace(tzinfo=None)


def test_now_bangkok_is_utc_plus_7(host_in_utc):
    assert abs(now_bangkok() - bangkok_now_from_utc()) < timedelta(seconds=5)
    assert abs((now_bangkok() - datetime.now(timezone.utc).replace(tzinfo=None)) - timedelta(hours=7)) < timedelta(seconds=5)
    assert today_bangkok() == bangkok_now_from_utc().date()


def test_submission_and_decision_use_bangkok_time_on_utc_host(client, db_session, host_in_utc):
    db_session.add(Student(student_id=STUDENT_ID, first_name="สมชาย", last_name="ใจดี", email="s@cmu.ac.th",
                           faculty="Faculty of Science", major="เคมี"))
    db_session.commit()

    response = client.post(
        "/api/student/me/external-activities",
        headers={"X-Student-Id": STUDENT_ID},
        data={"title": "Camp", "organization": "NGO", "activity_type": "จิตอาสา / บริการสังคม",
              "start_date": "2026-02-01", "end_date": "2026-02-01", "location": "CM", "role": "participant",
              "description": "", "skills": json.dumps({"volunteerism": 3})},
        files={"evidence": ("e.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201
    external_id = response.json()["id"]

    decision = client.patch(f"/api/external-activities/{external_id}/decision", json={"status": "approved"})
    assert decision.status_code == 200

    db_session.expire_all()
    external = db_session.get(ExternalActivity, external_id)
    expected = bangkok_now_from_utc()
    assert abs(external.submitted_at - expected) < timedelta(minutes=1)
    assert abs(external.decided_at - expected) < timedelta(minutes=1)
    # สองเวลาเกิดห่างกันไม่กี่วินาที ต้องไม่ต่างกัน 7 ชั่วโมงแบบเดิม
    assert abs(external.decided_at - external.submitted_at) < timedelta(minutes=1)
    assert external.submitted_at.date() == today_bangkok()

    # created_at ของนักศึกษาใช้เวลาไทยเหมือนกัน
    assert abs(db_session.get(Student, STUDENT_ID).created_at - expected) < timedelta(minutes=1)

    # "อนุมัติวันนี้" นับตามวันไทย
    stats = client.get("/api/requests/stats").json()
    assert stats["approved_today"] == 1


def test_admin_notification_time_has_bangkok_offset(client, db_session):
    db_session.add(Student(student_id=STUDENT_ID, first_name="สมชาย", last_name="ใจดี", email="s@cmu.ac.th",
                           faculty="Faculty of Science", major="เคมี"))
    db_session.commit()
    client.post(
        "/api/student/me/external-activities",
        headers={"X-Student-Id": STUDENT_ID},
        data={"title": "Camp", "organization": "NGO", "activity_type": "จิตอาสา / บริการสังคม",
              "start_date": "2026-02-01", "end_date": "2026-02-01", "location": "CM", "role": "participant",
              "description": "", "skills": json.dumps({"volunteerism": 3})},
        files={"evidence": ("e.png", PNG_BYTES, "image/png")},
    )

    created = client.get("/api/admin/notifications").json()["notifications"][0]["created_at"]
    parsed = datetime.fromisoformat(created)
    assert parsed.utcoffset() == timedelta(hours=7)
    assert abs(parsed - datetime.now(timezone.utc)) < timedelta(minutes=1)
