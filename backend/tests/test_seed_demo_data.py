from datetime import date, datetime

import academic_calendar
from models import Activity, ActivityMember, Student
from seed_demo_data import is_demo_student_id, remove_demo_data, seed_demo_data


def add_real_data(db_session):
    db_session.add(
        Student(
            student_id="670510659",
            first_name="Real",
            last_name="Student",
            email="real@cmu.ac.th",
            faculty="Faculty of Science",
            major="",
        )
    )
    db_session.add(
        Activity(
            activity_type="Volunteer",
            name="Real Activity",
            start_at=datetime(2026, 9, 3, 9, 0, 0),
            end_at=datetime(2026, 9, 3, 12, 0, 0),
            responsible_person="Staff",
            location="Room 101",
        )
    )
    db_session.commit()


def test_demo_student_id_pattern():
    assert is_demo_student_id("690519101")
    assert not is_demo_student_id("670510659")
    assert not is_demo_student_id("6905191")


def test_seed_creates_demo_data_and_remove_keeps_real_data(db_session):
    add_real_data(db_session)

    result = seed_demo_data(db_session, today=date(2026, 9, 28))

    assert result == {
        "students": 60,
        "activities": 19,
        "major_activities": 11,
        "memberships": result["memberships"],
        "mock_student_activities": 9,
        "year": 2026,
    }
    assert result["memberships"] >= 60 * 2

    # กิจกรรมคณะ 8 กิจกรรมไม่มีเจ้าของสาขา, กิจกรรมสาขามีครบทุกสาขา
    demo_activities = db_session.query(Activity).filter(Activity.name.startswith("[Demo] ")).all()
    assert sum(1 for activity in demo_activities if activity.major is None) == 8
    assert {activity.major for activity in demo_activities if activity.major} == {
        "เคมี", "ฟิสิกส์และวัสดุศาสตร์", "วิทยาการคอมพิวเตอร์", "ชีววิทยา", "สถิติ",
    }

    # นักศึกษาส่วนใหญ่เข้ากิจกรรมสาขาของตัวเอง
    major_members = (
        db_session.query(ActivityMember, Activity.major, Student.major)
        .join(Activity, Activity.id == ActivityMember.activity_id)
        .join(Student, Student.student_id == ActivityMember.student_id)
        .filter(Activity.major.isnot(None), ActivityMember.student_id != "670510659")
        .all()
    )
    own = sum(1 for _m, activity_major, student_major in major_members if activity_major == student_major)
    assert own > 0 and own >= len(major_members) * 0.7

    # นักศึกษาจำลองของหน้าฝั่งนักศึกษาได้เข้ากิจกรรม demo และได้สาขา (เดิมว่าง)
    mock_student = db_session.get(Student, "670510659")
    assert mock_student.major == "เคมี"
    assert db_session.query(ActivityMember).filter_by(student_id="670510659").count() == 9

    demo_students = [
        student for student in db_session.query(Student).all()
        if is_demo_student_id(student.student_id)
    ]
    assert len(demo_students) == 60
    # ปี 1-4 ในปีการศึกษา 2569 = รหัส 69, 68, 67, 66
    assert {student.student_id[:2] for student in demo_students} == {"69", "68", "67", "66"}

    # ปี 1 (รหัส 69) ต้องไม่อยู่ในกิจกรรมก่อนเดือนเริ่มปีการศึกษา (ก.ค.)
    first_year_early = (
        db_session.query(ActivityMember)
        .join(Activity, Activity.id == ActivityMember.activity_id)
        .filter(ActivityMember.student_id.like("69%"))
        .all()
    )
    assert all(
        member.activity.start_at.month >= academic_calendar.ACADEMIC_YEAR_START_MONTH
        for member in first_year_early
    )

    # รันซ้ำได้ ไม่ซ้ำซ้อน
    seed_demo_data(db_session, today=date(2026, 9, 28))
    assert db_session.query(Activity).filter(Activity.name.startswith("[Demo] ")).count() == 19

    students_removed, activities_removed = remove_demo_data(db_session)
    assert (students_removed, activities_removed) == (60, 19)

    assert [student.student_id for student in db_session.query(Student).all()] == ["670510659"]
    assert [activity.name for activity in db_session.query(Activity).all()] == ["Real Activity"]
    # การเข้าร่วมกิจกรรม demo ของนักศึกษาจำลองถูกลบตามกิจกรรมไปด้วย
    assert db_session.query(ActivityMember).filter_by(student_id="670510659").count() == 0
