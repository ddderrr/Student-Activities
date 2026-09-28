from datetime import date, datetime

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

    assert result == {"students": 60, "activities": 8, "memberships": result["memberships"], "year": 2026}
    assert result["memberships"] >= 60 * 2

    demo_students = [
        student for student in db_session.query(Student).all()
        if is_demo_student_id(student.student_id)
    ]
    assert len(demo_students) == 60
    # ปี 1-4 ในปีการศึกษา 2569 = รหัส 69, 68, 67, 66
    assert {student.student_id[:2] for student in demo_students} == {"69", "68", "67", "66"}

    # ปี 1 (รหัส 69) ต้องไม่อยู่ในกิจกรรมก่อน ก.ค.
    first_year_early = (
        db_session.query(ActivityMember)
        .join(Activity, Activity.id == ActivityMember.activity_id)
        .filter(ActivityMember.student_id.like("69%"))
        .all()
    )
    assert all(member.activity.start_at.month >= 7 for member in first_year_early)

    # รันซ้ำได้ ไม่ซ้ำซ้อน
    seed_demo_data(db_session, today=date(2026, 9, 28))
    assert db_session.query(Activity).filter(Activity.name.startswith("[Demo] ")).count() == 8

    students_removed, activities_removed = remove_demo_data(db_session)
    assert (students_removed, activities_removed) == (60, 8)

    assert [student.student_id for student in db_session.query(Student).all()] == ["670510659"]
    assert [activity.name for activity in db_session.query(Activity).all()] == ["Real Activity"]
