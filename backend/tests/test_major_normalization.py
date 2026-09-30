"""ค่า major ต้องถูก normalize ตอนบันทึก: ตัดช่องว่างหน้า-หลัง และค่าว่าง = ไม่มีสาขา

- activities.major: ค่าว่าง -> NULL (NULL = กิจกรรมส่วนกลางของคณะ)
- students.major:   ค่าว่าง -> "" (คอลัมน์เป็น NOT NULL ทั้งระบบใช้ "" แทนไม่มีสาขา)
"""

from datetime import datetime

import pytest

import admin_accounts
from major_utils import normalize_major
from models import Activity, ActivityMember, Student
from tests.conftest import CENTRAL_ADMIN_EMAIL

CHEM = "เคมี"


@pytest.mark.parametrize(
    "value, expected",
    [(" เคมี ", CHEM), (CHEM, CHEM), ("", None), ("   ", None), (None, None), ("\tเคมี\n", CHEM)],
)
def test_normalize_major(value, expected):
    assert normalize_major(value) == expected


def stored(db_session, model, key):
    db_session.expire_all()
    return db_session.get(model, key).major


def add_activity(db_session, major):
    activity = Activity(
        activity_type="Workshop",
        name="Activity",
        start_at=datetime(2026, 7, 1, 9),
        end_at=datetime(2026, 7, 1, 16),
        responsible_person="Staff",
        location="SCB1100",
        major=major,
    )
    db_session.add(activity)
    db_session.commit()
    return activity.id


@pytest.mark.parametrize("value, expected", [(" เคมี ", CHEM), ("", None), ("   ", None), (None, None)])
def test_activity_major_is_normalized_on_save(db_session, value, expected):
    activity_id = add_activity(db_session, value)

    assert stored(db_session, Activity, activity_id) == expected


def test_activity_major_is_normalized_on_update(db_session):
    activity_id = add_activity(db_session, CHEM)
    activity = db_session.get(Activity, activity_id)

    activity.major = "  "
    db_session.commit()
    assert stored(db_session, Activity, activity_id) is None

    activity.major = " วิทยาการคอมพิวเตอร์ "
    db_session.commit()
    assert stored(db_session, Activity, activity_id) == "วิทยาการคอมพิวเตอร์"


@pytest.mark.parametrize("value, expected", [(" เคมี ", CHEM), ("", ""), ("   ", ""), (None, "")])
def test_student_major_is_normalized_on_save(db_session, value, expected):
    db_session.add(
        Student(
            student_id="670510001",
            first_name="A",
            last_name="B",
            email="",
            faculty="Faculty of Science",
            major=value,
        )
    )
    db_session.commit()

    assert stored(db_session, Student, "670510001") == expected


# ------------------------------------------------------------
# ผ่าน endpoint ที่เขียน major จริง
# ------------------------------------------------------------


ACTIVITY_PAYLOAD = {
    "activity_type": "Workshop",
    "name": "กิจกรรมทดสอบ",
    "start_at": "2026-07-01T09:00:00",
    "end_at": "2026-07-01T12:00:00",
    "responsible_person": "Staff",
    "location": "SCB1100",
}


def test_create_activity_stores_normalized_major(client, db_session, monkeypatch):
    # สาขาในรายชื่อแอดมินมีช่องว่างติดมา
    monkeypatch.setattr(
        admin_accounts,
        "ADMIN_ACCOUNTS",
        [{"email": "padded@test.local", "name": "Padded", "major": " เคมี "}],
    )

    response = client.post(
        "/api/activities",
        json=ACTIVITY_PAYLOAD,
        headers={"X-Admin-Email": "padded@test.local"},
    )

    assert response.status_code == 201
    assert stored(db_session, Activity, response.json()["id"]) == CHEM


def test_central_admin_activity_major_is_null(client, db_session):
    response = client.post(
        "/api/activities",
        json=ACTIVITY_PAYLOAD,
        headers={"X-Admin-Email": CENTRAL_ADMIN_EMAIL},
    )

    assert response.status_code == 201
    assert stored(db_session, Activity, response.json()["id"]) is None


def test_participant_update_stores_normalized_student_major(client, db_session):
    activity_id = add_activity(db_session, None)
    db_session.add(
        Student(student_id="670510002", first_name="A", last_name="B", email="", faculty="x", major=CHEM)
    )
    db_session.add(ActivityMember(activity_id=activity_id, student_id="670510002", role="participant"))
    db_session.commit()

    for value, expected in ((" เคมี ", CHEM), ("   ", "")):
        response = client.patch(
            f"/api/activities/{activity_id}/participants/670510002",
            json={
                "first_name": "A",
                "last_name": "B",
                "email": "",
                "faculty": "x",
                "major": value,
                "role": "participant",
            },
            headers={"X-Admin-Email": CENTRAL_ADMIN_EMAIL},
        )
        assert response.status_code == 200, response.text
        assert stored(db_session, Student, "670510002") == expected
