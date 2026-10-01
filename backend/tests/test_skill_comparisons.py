"""
My Skills: กราฟเปรียบเทียบแยก 2 แบบ
- major:   กิจกรรมของสาขาตัวเอง vs ค่าเฉลี่ยนักศึกษาสาขาเดียวกัน
- faculty: กิจกรรมของคณะ (Activity.major = None) vs ค่าเฉลี่ยนักศึกษาทั้งคณะ
กิจกรรมภายนอกและกิจกรรมของสาขาอื่นไม่นับเข้ากราฟทั้งสองแบบ
"""

from datetime import date, datetime

from models import (
    Activity,
    ActivityMember,
    ActivitySkill,
    ExternalActivity,
    ExternalActivitySkill,
    Student,
)


def add_student(db_session, student_id, major):
    db_session.add(
        Student(
            student_id=student_id,
            first_name="Test",
            last_name=student_id,
            email=f"{student_id}@test.local",
            faculty="Faculty of Science",
            major=major,
        )
    )


def add_activity(db_session, name, major, level, members):
    activity = Activity(
        activity_type="Volunteer",
        name=name,
        start_at=datetime(2026, 8, 1, 9, 0, 0),
        end_at=datetime(2026, 8, 1, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
        major=major,
        skill_levels=[
            ActivitySkill(skill_key="volunteerism", target_role="participant", level=level),
        ],
    )
    db_session.add(activity)
    db_session.commit()

    db_session.add_all([
        ActivityMember(activity_id=activity.id, student_id=student_id, role="participant")
        for student_id in members
    ])
    db_session.commit()


def seed(db_session):
    add_student(db_session, "670510001", "เคมี")
    add_student(db_session, "670510002", "เคมี")
    add_student(db_session, "670510003", "ฟิสิกส์")
    db_session.commit()

    add_activity(db_session, "Chem 1", "เคมี", 5, ["670510001"])
    add_activity(db_session, "Chem 2", "เคมี", 3, ["670510002"])
    add_activity(db_session, "Physics", "ฟิสิกส์", 1, ["670510001", "670510003"])
    add_activity(db_session, "Faculty 1", None, 2, ["670510001"])
    add_activity(db_session, "Faculty 2", None, 4, ["670510003"])

    external = ExternalActivity(
        student_id="670510001",
        title="Outside",
        organization="Outside Org",
        activity_type="Volunteer",
        start_date=date(2026, 8, 2),
        end_date=date(2026, 8, 2),
        location="Outside",
        role="participant",
        status="approved",
    )
    db_session.add(external)
    db_session.commit()
    db_session.add(
        ExternalActivitySkill(
            external_activity_id=external.id,
            skill_key="volunteerism",
            target_role="participant",
            level=1,
        )
    )
    db_session.commit()


def add_external(db_session, student_id, level, status="approved"):
    external = ExternalActivity(
        student_id=student_id,
        title=f"Outside {student_id} {status}",
        organization="Outside Org",
        activity_type="Volunteer",
        start_date=date(2026, 8, 3),
        end_date=date(2026, 8, 3),
        location="Outside",
        role="participant",
        status=status,
    )
    db_session.add(external)
    db_session.commit()
    db_session.add(
        ExternalActivitySkill(
            external_activity_id=external.id,
            skill_key="volunteerism",
            target_role="participant",
            level=level,
        )
    )
    db_session.commit()


def my_period(client, student_id="670510001"):
    response = client.get(
        "/api/student/me/skills",
        headers={"X-Student-Id": student_id},
    )
    assert response.status_code == 200
    return response.json()["periods"]["year-2026"]


def test_major_comparison_uses_own_major_activities_and_major_average(client, db_session):
    seed(db_session)

    major = my_period(client)["comparisons"]["major"]

    # เฉพาะ Chem 1 (ไม่นับ Physics ของสาขาอื่น, Faculty และกิจกรรมภายนอก)
    assert major["skills"]["volunteerism"] == 5
    # นักศึกษาเคมี 2 คน: (5 + 3) / 2
    assert major["average"]["volunteerism"] == 4


def test_faculty_comparison_uses_faculty_activities_and_faculty_average(client, db_session):
    seed(db_session)

    faculty = my_period(client)["comparisons"]["faculty"]

    assert faculty["skills"]["volunteerism"] == 2
    # ทุกคนในคณะที่เข้ากิจกรรมคณะ: (2 + 4) / 2
    assert faculty["average"]["volunteerism"] == 3


def test_activities_are_tagged_with_scope(client, db_session):
    seed(db_session)

    scopes = {item["title"]: item["scope"] for item in my_period(client)["activities"]}

    assert scopes == {
        "Chem 1": "major",
        "Physics": "other_major",
        "Faculty 1": "faculty",
        "Outside": "external",
    }


def test_combined_skills_are_unchanged(client, db_session):
    seed(db_session)

    # skills รวม (ใช้กับ PDF export) ยังนับทุกกิจกรรมเหมือนเดิม: (5 + 1 + 2 + 1) / 4
    assert my_period(client)["skills"]["volunteerism"] == 2.25


def test_admin_report_splits_each_student_by_major_and_faculty(client, db_session):
    seed(db_session)

    body = client.get("/api/admin/student-skills?year=2026").json()
    by_id = {student["id"]: student for student in body["students"]}

    first = by_id["670510001"]
    # skills รวมยังนับทุกกิจกรรม: Chem 1, Physics, Faculty 1, Outside
    assert first["skills"]["volunteerism"] == 2.25
    assert first["majorSkills"]["volunteerism"] == 5
    assert first["facultySkills"]["volunteerism"] == 2

    physics = by_id["670510003"]
    assert physics["majorSkills"]["volunteerism"] == 1
    assert physics["facultySkills"]["volunteerism"] == 4

    assert by_id["670510002"]["facultySkills"]["volunteerism"] is None
    assert body["facultyActivityAverage"]["volunteerism"] == 3


def test_external_comparison_uses_approved_external_activities_only(client, db_session):
    seed(db_session)
    add_external(db_session, "670510003", 5)
    add_external(db_session, "670510003", 1, status="pending")  # ยังไม่อนุมัติ ไม่นับ

    external = my_period(client)["comparisons"]["external"]

    # ของฉัน: เฉพาะ Outside (ไม่นับกิจกรรมสาขา / คณะ)
    assert external["skills"]["volunteerism"] == 1
    # ทั้งคณะ แบบ student-first: (1 + 5) / 2
    assert external["average"]["volunteerism"] == 3


def test_admin_report_has_external_skills_and_average(client, db_session):
    seed(db_session)
    add_external(db_session, "670510003", 5)

    body = client.get("/api/admin/student-skills?year=2026").json()
    by_id = {student["id"]: student for student in body["students"]}

    assert by_id["670510001"]["externalSkills"]["volunteerism"] == 1
    assert by_id["670510003"]["externalSkills"]["volunteerism"] == 5
    assert by_id["670510002"]["externalSkills"]["volunteerism"] is None
    # กิจกรรมภายนอกไม่ปนในกราฟสาขา / คณะ
    assert by_id["670510003"]["facultySkills"]["volunteerism"] == 4
    assert body["externalActivityAverage"]["volunteerism"] == 3


def test_student_without_major_has_empty_major_comparison(client, db_session):
    seed(db_session)
    add_student(db_session, "670510009", "")
    db_session.commit()
    add_activity(db_session, "Faculty 3", None, 3, ["670510009"])

    period = my_period(client, "670510009")
    major = period["comparisons"]["major"]

    assert period["comparisons"]["faculty"]["skills"]["volunteerism"] == 3

    assert major["skills"]["volunteerism"] is None
    assert major["average"]["volunteerism"] is None
