from datetime import date, datetime

import academic_calendar

from main import report_academic_year_be, student_entry_year_be, student_year_level
from models import Activity, ActivityMember, ActivitySkill, Student


def test_student_entry_year_be_reads_first_two_digits():
    assert student_entry_year_be("670510670") == 2567
    assert student_entry_year_be(" 690510001 ") == 2569
    assert student_entry_year_be("X10510001") is None
    # isdigit() ผ่านแต่ int() แปลงไม่ได้ ต้องไม่ทำให้ทั้งรายงาน error
    assert student_entry_year_be("²3" + "0510001") is None
    assert student_entry_year_be("") is None
    assert student_entry_year_be(None) is None


def test_report_academic_year_starts_in_july():
    today = date(2026, 9, 28)

    # ม.ค.-มิ.ย. 2026 ยังเป็นปีการศึกษา 2568, ก.ค.-ธ.ค. 2026 เป็น 2569
    assert report_academic_year_be(2026, "SEMESTER_1", today) == 2568
    assert report_academic_year_be(2026, "SEMESTER_2", today) == 2569

    # ทั้งปี: ใช้ชั้นปีล่าสุดของปีนั้น
    assert report_academic_year_be(2025, "ALL", today) == 2568
    assert report_academic_year_be(2026, "ALL", today) == 2569

    # ปีปัจจุบันแต่ยังไม่ถึง ก.ค. = ชั้นปีปัจจุบัน
    assert report_academic_year_be(2026, "ALL", date(2026, 3, 1)) == 2568


def test_report_academic_year_follows_shared_start_month(monkeypatch):
    # ใช้เดือนเริ่มปีการศึกษาเดียวกับ transcript (academic_calendar.py)
    monkeypatch.setattr(academic_calendar, "ACADEMIC_YEAR_START_MONTH", 8)

    assert report_academic_year_be(2026, "ALL", date(2026, 7, 31)) == 2568
    assert report_academic_year_be(2026, "ALL", date(2026, 8, 1)) == 2569


def test_student_year_level_is_class_standing():
    assert student_year_level(2569, 2569) == 1
    assert student_year_level(2567, 2569) == 3
    assert student_year_level(2560, 2569) == 10
    # ยังไม่ได้เข้าเรียนในปีการศึกษานั้น
    assert student_year_level(2570, 2569) is None
    assert student_year_level(None, 2569) is None


def add_student(db_session, student_id, major):
    db_session.add(
        Student(
            student_id=student_id,
            first_name="Test",
            last_name=student_id,
            email=f"{student_id}@cmu.ac.th",
            faculty="Faculty of Science",
            major=major,
        )
    )


def add_activity_with_members(db_session, start_at, member_ids):
    activity = Activity(
        activity_type="Volunteer",
        name="Skill Activity",
        start_at=start_at,
        end_at=start_at,
        responsible_person="Staff Name",
        location="Room 101",
    )
    db_session.add(activity)
    db_session.commit()

    db_session.add(
        ActivitySkill(
            activity_id=activity.id,
            skill_key="volunteerism",
            target_role="participant",
            level=4,
        )
    )

    for student_id in member_ids:
        db_session.add(
            ActivityMember(
                activity_id=activity.id,
                student_id=student_id,
                role="participant",
            )
        )

    db_session.commit()


def population_of(body):
    return {
        (item["yearLevel"], item["major"]): item["count"]
        for item in body["population"]
    }


def test_student_skills_report_includes_year_level_major_and_population(
    client,
    db_session,
):
    add_student(db_session, "670510001", "Chemistry")
    add_student(db_session, "680510002", "Physics")
    add_student(db_session, "690510003", "")
    add_student(db_session, "700510004", "Chemistry")  # เข้าปี 2570: ยังไม่เข้าเรียนในปีการศึกษา 2569
    add_student(db_session, "X0510005", "Physics")  # รหัสอ่านปีที่เข้าไม่ได้
    db_session.commit()

    add_activity_with_members(
        db_session,
        datetime(2026, 8, 1, 9, 0, 0),
        ["670510001", "680510002"],
    )

    response = client.get("/api/admin/student-skills?year=2026&semester=SEMESTER_2")

    assert response.status_code == 200
    body = response.json()

    by_id = {student["id"]: student for student in body["students"]}
    assert by_id["670510001"]["yearLevel"] == 3
    assert by_id["670510001"]["major"] == "Chemistry"
    assert by_id["680510002"]["yearLevel"] == 2
    assert by_id["680510002"]["skills"]["volunteerism"] == 4

    assert population_of(body) == {
        (3, "Chemistry"): 1,
        (2, "Physics"): 1,
        (1, ""): 1,
        (None, "Physics"): 1,
    }


def test_semester_1_uses_previous_academic_year(client, db_session):
    add_student(db_session, "680510002", "Physics")
    add_student(db_session, "650510009", "Chemistry")
    add_student(db_session, "690510003", "Physics")  # ยังไม่เข้าเรียนใน ม.ค.-มิ.ย. 2026
    db_session.commit()

    add_activity_with_members(
        db_session,
        datetime(2026, 2, 10, 9, 0, 0),
        ["680510002", "650510009"],
    )

    response = client.get("/api/admin/student-skills?year=2026&semester=SEMESTER_1")

    assert response.status_code == 200
    body = response.json()

    by_id = {student["id"]: student for student in body["students"]}
    # ก.พ. 2026 = ปีการศึกษา 2568: รหัส 68 เป็นปี 1, รหัส 65 เป็นปี 4 (ยังไม่ใช่ปี 5)
    assert by_id["680510002"]["yearLevel"] == 1
    assert by_id["650510009"]["yearLevel"] == 4

    assert population_of(body) == {
        (1, "Physics"): 1,
        (4, "Chemistry"): 1,
    }


def test_evidence_before_entry_year_is_counted_in_population(client, db_session):
    # รหัส 69 มีกิจกรรมใน ก.พ. 2026 ก่อนเข้าเรียน (ปีการศึกษา 2569 เริ่ม ก.ค. 2026)
    add_student(db_session, "690510003", "Physics")
    db_session.commit()

    add_activity_with_members(
        db_session,
        datetime(2026, 2, 10, 9, 0, 0),
        ["690510003"],
    )

    response = client.get("/api/admin/student-skills?year=2026&semester=SEMESTER_1")

    assert response.status_code == 200
    body = response.json()

    assert [student["yearLevel"] for student in body["students"]] == [None]

    # จำนวนที่มีข้อมูล skill ต้องไม่เกินจำนวนนักศึกษาในกลุ่มเดียวกัน
    assert population_of(body) == {(None, "Physics"): 1}
