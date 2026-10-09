"""ปฏิทินกิจกรรมท้ายหน้า Dashboard: GET /api/admin/calendar/activities"""

from datetime import datetime

from models import Activity, ActivityMember, Student
from tests.conftest import CENTRAL_ADMIN_EMAIL, CHEM_ADMIN_EMAIL

URL = "/api/admin/calendar/activities"
CHEM = "เคมี"
CS = "วิทยาการคอมพิวเตอร์"


def make_activity(db_session, name, major):
    activity = Activity(activity_type="สัมมนา", name=name, start_at=datetime(2026, 10, 1, 9),
                        end_at=datetime(2026, 10, 2, 23, 59), department="ผู้จัด",
                        responsible_person="อาจารย์", location="CMU", major=major)
    db_session.add(activity)
    db_session.commit()
    return activity


def names(response):
    assert response.status_code == 200
    return sorted(item["name"] for item in response.json()["activities"])


def seed(db_session):
    chem = make_activity(db_session, "Chem Day", CHEM)
    make_activity(db_session, "CS Day", CS)
    make_activity(db_session, "Faculty Day", None)
    db_session.add(Student(student_id="670510001", first_name="A", last_name="B", email="a@cmu.ac.th",
                           faculty="Faculty of Science", major=CS))
    db_session.commit()
    db_session.add(ActivityMember(activity_id=chem.id, student_id="670510001", role="participant"))
    db_session.commit()


def test_central_admin_sees_all_or_one_branch(client, db_session):
    seed(db_session)
    central = {"X-Admin-Email": CENTRAL_ADMIN_EMAIL}

    assert names(client.get(URL, headers=central)) == ["CS Day", "Chem Day", "Faculty Day"]
    assert names(client.get(URL, params={"major": CHEM}, headers=central)) == ["Chem Day"]
    assert all(item["can_open"] for item in client.get(URL, headers=central).json()["activities"])


def test_branch_admin_can_toggle_between_all_and_own_branch(client, db_session):
    seed(db_session)
    chem = {"X-Admin-Email": CHEM_ADMIN_EMAIL}

    everything = client.get(URL, headers=chem).json()["activities"]
    assert sorted(item["name"] for item in everything) == ["CS Day", "Chem Day", "Faculty Day"]
    # เปิดรายละเอียดได้เฉพาะกิจกรรมของสาขาตัวเองและกิจกรรมส่วนกลาง
    assert {item["name"]: item["can_open"] for item in everything} == {
        "CS Day": False, "Chem Day": True, "Faculty Day": True,
    }
    # จำนวนผู้เข้าร่วมนับทุกคน ไม่จำกัดตามสาขาของแอดมิน
    assert next(item for item in everything if item["name"] == "Chem Day")["participants"] == 1

    assert names(client.get(URL, params={"scope": "mine"}, headers=chem)) == ["Chem Day"]
    # แอดมินสาขาส่ง major มาเองไม่มีผล
    assert len(client.get(URL, params={"major": CS, "scope": "mine"}, headers=chem).json()["activities"]) == 1


def test_validation_and_auth(client):
    assert client.get(URL, params={"scope": "other"}).status_code == 400
    assert client.get(URL, headers={"X-Admin-Email": ""}).status_code in (401, 403)
