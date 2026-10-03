"""แท็บในหน้า My Activities: กิจกรรมคณะ vs กิจกรรมภายนอก (GET /api/student/me/activities)

แอดมินสาขาเพิ่มนักศึกษาสาขาอื่นเข้ากิจกรรมของตัวเองได้ นักศึกษาคนนั้นต้องเห็นกิจกรรมนี้
เป็น "กิจกรรมภายนอก" ส่วนกิจกรรมของสาขาตัวเองและกิจกรรมส่วนกลาง (ไม่มีสาขา) เป็น
"กิจกรรมคณะ" กฎเดียวกับ skill_scoring.activity_source
"""

from datetime import date, datetime

from models import Activity, ExternalActivity, Student
from tests.conftest import CENTRAL_ADMIN_EMAIL, CHEM_ADMIN_EMAIL, CS_ADMIN_EMAIL

CS = "วิทยาการคอมพิวเตอร์"
CHEM = "เคมี"
CS_STUDENT = "670510101"
STUDENT_HEADERS = {"X-Student-Id": CS_STUDENT}


def make_activity(db_session, name, major) -> int:
    activity = Activity(
        activity_type="Volunteer",
        name=name,
        start_at=datetime(2026, 1, 10, 9),
        end_at=datetime(2026, 1, 10, 12),
        responsible_person="Staff",
        location="Room 101",
        major=major,
    )
    db_session.add(activity)
    db_session.commit()
    return activity.id


def add_participant(client, activity_id, admin_email):
    # ทางเดียวกับปุ่ม "เพิ่มผู้เข้าร่วม" / import ในหน้า Activities ของแอดมิน
    response = client.post(
        f"/api/activities/{activity_id}/participants/import/confirm",
        json={"students": [{"student_id": CS_STUDENT, "first_name": "สมชาย", "last_name": "ใจดี", "role": "participant"}]},
        headers={"X-Admin-Email": admin_email},
    )
    assert response.status_code in (200, 201), response.text


def make_external(db_session, title, status):
    db_session.add(
        ExternalActivity(
            student_id=CS_STUDENT,
            title=title,
            organization="NGO",
            activity_type="จิตอาสา / บริการสังคม",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 1),
            location="Chiang Mai",
            role="participant",
            status=status,
        )
    )
    db_session.commit()


def my_activities(client):
    response = client.get("/api/student/me/activities", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    return {item["title"]: item for item in response.json()["activities"]}


def setup_cs_student(db_session):
    db_session.add(
        Student(student_id=CS_STUDENT, first_name="สมชาย", last_name="ใจดี",
                email="somchai@cmu.ac.th", faculty="Faculty of Science", major=CS)
    )
    db_session.commit()


def test_cs_student_in_cs_activity_is_faculty(client, db_session):
    setup_cs_student(db_session)
    add_participant(client, make_activity(db_session, "CS Camp", CS), CS_ADMIN_EMAIL)

    item = my_activities(client)["CS Camp"]

    assert (item["category"], item["scope"], item["source"]) == ("faculty", "major", "activity")


def test_cs_student_added_by_chem_admin_is_external(client, db_session):
    setup_cs_student(db_session)
    add_participant(client, make_activity(db_session, "Chem Lab", CHEM), CHEM_ADMIN_EMAIL)

    item = my_activities(client)["Chem Lab"]

    assert (item["category"], item["scope"], item["activity_major"]) == ("external", "other_major", CHEM)
    # ยังเป็นกิจกรรมของคณะ (ไม่ใช่คำขอที่นักศึกษาส่งเอง): source ไม่เปลี่ยน
    assert item["source"] == "activity"


def test_activity_without_major_is_faculty(client, db_session):
    setup_cs_student(db_session)
    add_participant(client, make_activity(db_session, "Faculty Day", None), CENTRAL_ADMIN_EMAIL)
    add_participant(client, make_activity(db_session, "Blank Major", "   "), CENTRAL_ADMIN_EMAIL)

    items = my_activities(client)

    assert (items["Faculty Day"]["category"], items["Faculty Day"]["scope"]) == ("faculty", "faculty")
    assert items["Blank Major"]["category"] == "faculty"


def test_approved_external_activity_is_external_and_pending_is_not_listed(client, db_session):
    setup_cs_student(db_session)
    make_external(db_session, "Beach Cleanup", "approved")
    make_external(db_session, "Still Waiting", "pending")

    items = my_activities(client)

    assert (items["Beach Cleanup"]["category"], items["Beach Cleanup"]["source"]) == ("external", "external_activity")
    # คำขอที่ยังไม่อนุมัติอยู่ในแท็บ "รายการที่ส่ง" (GET /api/student/me/external-activities)
    assert "Still Waiting" not in items


def test_student_without_major_sees_branch_activities_as_external(client, db_session):
    setup_cs_student(db_session)
    db_session.get(Student, CS_STUDENT).major = ""
    db_session.commit()
    add_participant(client, make_activity(db_session, "Chem Lab", CHEM), CENTRAL_ADMIN_EMAIL)

    assert my_activities(client)["Chem Lab"]["category"] == "external"


def test_mixed_list_counts(client, db_session):
    setup_cs_student(db_session)
    add_participant(client, make_activity(db_session, "CS Camp", CS), CS_ADMIN_EMAIL)
    add_participant(client, make_activity(db_session, "Faculty Day", None), CENTRAL_ADMIN_EMAIL)
    add_participant(client, make_activity(db_session, "Chem Lab", CHEM), CHEM_ADMIN_EMAIL)
    make_external(db_session, "Beach Cleanup", "approved")

    categories = [item["category"] for item in my_activities(client).values()]

    assert categories.count("faculty") == 2
    assert categories.count("external") == 2
