from datetime import datetime

from models import Activity, ActivityMember, Student
from tests.test_students_import_legacy_xls import (
    XLS_CONTENT_TYPE,
    build_legacy_xls,
)


def create_activity(db_session) -> Activity:
    activity = Activity(
        activity_type="Volunteer",
        name="Test Activity",
        start_at=datetime(2026, 1, 10, 9, 0, 0),
        end_at=datetime(2026, 1, 10, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def create_existing_student(db_session) -> Student:
    student = Student(
        student_id="670510670",
        first_name="จักริน",
        last_name="ชวชาติ",
        email="jakkarin@cmu.ac.th",
        faculty="คณะวิทยาศาสตร์",
        major="วิทยาการคอมพิวเตอร์",
    )
    db_session.add(student)
    db_session.commit()
    return student


def confirm(client, activity_id, students):
    return client.post(
        f"/api/activities/{activity_id}/participants/import/confirm",
        json={"students": students},
    )


def reload_student(db_session) -> Student:
    db_session.expire_all()
    return db_session.get(Student, "670510670")


def test_legacy_xls_import_keeps_existing_email_major_and_faculty(client, db_session):
    activity = create_activity(db_session)
    create_existing_student(db_session)

    # ไฟล์ .xls จากระบบเช็คอินเก่า: มีแค่รหัส ชื่อ และคณะ (คณะว่างในแถวนี้)
    content = build_legacy_xls([[1, "670510670", "จักริน ชวชาติ", "", "10:05:00"]])
    preview = client.post(
        f"/api/activities/{activity.id}/participants/import/preview",
        files={"file": ("checkin.xls", content, XLS_CONTENT_TYPE)},
    )
    assert preview.status_code == 200
    assert preview.json()["students"][0]["email"] == ""

    response = confirm(client, activity.id, preview.json()["students"])

    assert response.status_code == 200, response.text
    student = reload_student(db_session)
    assert student.email == "jakkarin@cmu.ac.th"
    assert student.major == "วิทยาการคอมพิวเตอร์"
    assert student.faculty == "คณะวิทยาศาสตร์"
    assert db_session.get(ActivityMember, (activity.id, "670510670")) is not None


def test_blank_or_missing_optional_fields_keep_existing_values(client, db_session):
    activity = create_activity(db_session)
    create_existing_student(db_session)

    response = confirm(
        client,
        activity.id,
        [
            {
                "student_id": "670510670",
                "first_name": "จักริน",
                "last_name": "ชวชาติ",
                "email": "   ",
                "faculty": "",
                # ไม่มี key major เลย
            }
        ],
    )

    assert response.status_code == 200, response.text
    student = reload_student(db_session)
    assert student.email == "jakkarin@cmu.ac.th"
    assert student.major == "วิทยาการคอมพิวเตอร์"
    assert student.faculty == "คณะวิทยาศาสตร์"


def test_values_in_file_still_update_existing_student(client, db_session):
    activity = create_activity(db_session)
    create_existing_student(db_session)

    response = confirm(
        client,
        activity.id,
        [
            {
                "student_id": "670510670",
                "first_name": "จักรินทร์",
                "last_name": "ชวชาติ",
                "email": "new@cmu.ac.th",
                "faculty": "คณะวิศวกรรมศาสตร์",
                "major": "วิศวกรรมคอมพิวเตอร์",
            }
        ],
    )

    assert response.status_code == 200
    student = reload_student(db_session)
    assert student.first_name == "จักรินทร์"
    assert student.email == "new@cmu.ac.th"
    assert student.faculty == "คณะวิศวกรรมศาสตร์"
    assert student.major == "วิศวกรรมคอมพิวเตอร์"


def test_new_student_without_optional_fields_uses_defaults(client, db_session):
    activity = create_activity(db_session)

    response = confirm(
        client,
        activity.id,
        [{"student_id": "670510999", "first_name": "ใหม่", "last_name": "ทดสอบ", "email": "", "faculty": ""}],
    )

    assert response.status_code == 200
    db_session.expire_all()
    student = db_session.get(Student, "670510999")
    assert student.email == ""
    assert student.major == ""
    assert student.faculty == "Faculty of Science"
