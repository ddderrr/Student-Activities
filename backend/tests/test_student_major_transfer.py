"""ย้ายสาขา: ประวัติของนักศึกษาไม่เปลี่ยน เปลี่ยนแค่ค่าเฉลี่ยที่ใช้ "เทียบสาขา"

ข้อมูล: 670510001 อยู่เคมี ทำกิจกรรมเคมี (level 5) และกิจกรรมคณะ (level 2)
แล้วย้ายไปวิทยาการคอมพิวเตอร์ (CS)
"""

from datetime import datetime

from activity_hours import activity_hours_summary
from major_history import change_student_major, major_at
from models import Activity, ActivityMember, ActivitySkill, Student, StudentMajorHistory
from tests.conftest import CHEM_ADMIN_EMAIL
from tests.test_skill_comparisons import add_activity, add_student, my_period
from transcript_data import load_internal_items


CHEM = "เคมี"
CS = "วิทยาการคอมพิวเตอร์"
MOVER = "670510001"
URL = f"/api/admin/students/{MOVER}"


def seed(db_session):
    add_student(db_session, MOVER, CHEM)
    add_student(db_session, "670510002", CHEM)
    add_student(db_session, "670510003", CS)
    db_session.commit()

    add_activity(db_session, "Chem 1", CHEM, 5, [MOVER])
    add_activity(db_session, "Chem 2", CHEM, 3, ["670510002"])
    add_activity(db_session, "CS 1", CS, 1, ["670510003"])
    add_activity(db_session, "Faculty 1", None, 2, [MOVER])


def payload(major=CS, **overrides):
    return {"first_name": "Test", "last_name": MOVER, "email": f"{MOVER}@test.local", "major": major, **overrides}


def snapshot(client, db_session):
    period = my_period(client, MOVER)
    student = db_session.get(Student, MOVER)
    return {
        "skills": {key: value["skills"] for key, value in period["comparisons"].items()},
        "scopes": {item["title"]: item["scope"] for item in period["activities"]},
        "hours": activity_hours_summary(db_session, student),
        "transcript": {item["title"]: item["source"] for item in load_internal_items(db_session, student)},
    }


def test_own_skills_hours_and_transcript_do_not_change_after_transfer(client, db_session):
    seed(db_session)
    before = snapshot(client, db_session)

    assert client.patch(URL, json=payload()).status_code == 200
    db_session.expire_all()

    after = snapshot(client, db_session)
    assert after == before
    assert after["scopes"]["Chem 1"] == "major"
    assert after["skills"]["major"]["volunteerism"] == 5


def test_major_comparison_switches_to_current_major_average(client, db_session):
    seed(db_session)
    assert my_period(client, MOVER)["comparisons"]["major"]["average"]["volunteerism"] == 4  # (5 + 3) / 2

    client.patch(URL, json=payload())

    # เทียบกับค่าเฉลี่ย CS ปัจจุบัน: กิจกรรม CS ของคนที่อยู่ CS ตอนนั้น = 670510003 เท่านั้น
    assert my_period(client, MOVER)["comparisons"]["major"]["average"]["volunteerism"] == 1


def test_old_major_average_keeps_the_mover_history(client, db_session):
    seed(db_session)
    client.patch(URL, json=payload())

    # เคมีปี 2026 ยังนับกิจกรรมที่ 670510001 ทำตอนอยู่เคมี: (5 + 3) / 2
    assert my_period(client, "670510002")["comparisons"]["major"]["average"]["volunteerism"] == 4


def test_activities_after_transfer_use_new_major(client, db_session):
    seed(db_session)
    change_student_major(db_session, db_session.get(Student, MOVER), CS, now=datetime(2026, 9, 1))
    db_session.commit()

    for name, major in (("Chem later", CHEM), ("CS later", CS)):
        activity = Activity(
            activity_hours=3, activity_type="Volunteer", name=name, responsible_person="Staff",
            location="Room", major=major,
            start_at=datetime(2026, 9, 10, 9), end_at=datetime(2026, 9, 10, 12),
            skill_levels=[ActivitySkill(skill_key="volunteerism", target_role="participant", level=4)],
        )
        db_session.add(activity)
        db_session.commit()
        db_session.add(ActivityMember(activity_id=activity.id, student_id=MOVER, role="participant"))
    db_session.commit()

    scopes = {item["title"]: item["scope"] for item in my_period(client, MOVER)["activities"]}
    assert scopes["Chem 1"] == "major"
    assert scopes["Chem later"] == "other_major"
    assert scopes["CS later"] == "major"


def test_major_at_uses_history_ranges():
    history = [(datetime(2026, 1, 1), "A"), (datetime(2026, 6, 1), "B")]

    assert major_at("C", history, datetime(2025, 12, 31)) == "A"
    assert major_at("C", history, datetime(2026, 3, 1)) == "B"
    assert major_at("C", history, datetime(2026, 6, 1)) == "C"
    assert major_at("C", history, None) == "C"
    assert major_at(" C ", None, datetime(2020, 1, 1)) == "C"


def test_edit_returns_student_and_records_history(client, db_session):
    seed(db_session)

    response = client.patch(URL, json=payload(first_name=" New ", email="new@cmu.ac.th"))

    assert response.status_code == 200
    body = response.json()
    assert (body["first_name"], body["email"], body["major"], body["activity_count"]) == ("New", "new@cmu.ac.th", CS, 2)
    assert [row.major for row in db_session.query(StudentMajorHistory).all()] == [CHEM]


def test_saving_same_major_or_name_only_does_not_add_history(client, db_session):
    seed(db_session)

    assert client.patch(URL, json=payload(major=CHEM)).status_code == 200
    assert client.patch(URL, json=payload(major=None, first_name="Only name")).status_code == 200

    assert db_session.query(StudentMajorHistory).count() == 0


def test_branch_admin_can_edit_name_but_not_major(client, db_session):
    seed(db_session)
    branch = {"X-Admin-Email": CHEM_ADMIN_EMAIL}

    assert client.patch(URL, json=payload(), headers=branch).status_code == 403
    assert client.patch(URL, json=payload(major=CHEM, first_name="Renamed"), headers=branch).status_code == 200
    db_session.expire_all()
    assert db_session.get(Student, MOVER).first_name == "Renamed"


def test_branch_admin_cannot_edit_other_major_student(client, db_session):
    seed(db_session)

    response = client.patch(
        "/api/admin/students/670510003",
        json=payload(major=None),
        headers={"X-Admin-Email": CHEM_ADMIN_EMAIL},
    )
    assert response.status_code == 403


def test_validation(client, db_session):
    seed(db_session)

    assert client.patch(URL, json=payload(major="สาขาที่ไม่มี")).status_code == 400
    assert client.patch(URL, json=payload(first_name=" ")).status_code == 400
    assert client.patch(URL, json=payload(email="not-an-email")).status_code == 400
    assert client.patch("/api/admin/students/999", json=payload()).status_code == 404


def test_participant_edit_also_records_history(client, db_session):
    seed(db_session)
    activity_id = db_session.query(Activity.id).filter(Activity.name == "Chem 1").scalar()

    response = client.patch(
        f"/api/activities/{activity_id}/participants/{MOVER}",
        json={"first_name": "Test", "last_name": MOVER, "email": "", "faculty": "", "major": CS, "role": "participant"},
    )

    assert response.status_code == 200
    assert [row.major for row in db_session.query(StudentMajorHistory).all()] == [CHEM]


def test_deleting_student_removes_history(client, db_session):
    seed(db_session)
    client.patch(URL, json=payload())

    assert client.delete(URL).status_code == 200
    assert db_session.query(StudentMajorHistory).count() == 0
