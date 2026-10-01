from datetime import datetime

import pytest

from faculty_utils import DEFAULT_FACULTY, normalize_faculty
from models import Activity, Student
from tests.test_students_import import VALID_HEADERS, build_xlsx
from tests.test_students_import import upload as upload_xlsx
from tests.test_students_import_legacy_xls import build_legacy_xls
from tests.test_students_import_legacy_xls import upload as upload_legacy_xls


# ------------------------------------------------------------
# normalize_faculty()
# ------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "   ",
        "คณะวิทยาศาสตร์",
        "  คณะวิทยาศาสตร์  ",
        "Faculty of Science",
        "faculty of science",
        " FACULTY OF SCIENCE ",
    ],
)
def test_science_faculty_and_blank_become_default(value):
    assert normalize_faculty(value) == DEFAULT_FACULTY == "Faculty of Science"


def test_other_faculty_is_only_trimmed():
    assert normalize_faculty("  คณะวิศวกรรมศาสตร์ ") == "คณะวิศวกรรมศาสตร์"


# ------------------------------------------------------------
# POST /api/students/import (.xlsx และ .xls เช็คอินเก่า)
# ------------------------------------------------------------


def test_xlsx_import_normalizes_faculty(client, db_session):
    rows = [
        ["640610001", "A", "One", "a@cmu.ac.th", "  คณะวิทยาศาสตร์ ", "CS"],
        ["640610002", "B", "Two", "b@cmu.ac.th", "FACULTY OF SCIENCE", "CS"],
        ["640610003", "C", "Three", "c@cmu.ac.th", "", "CS"],
        ["640610004", "D", "Four", "d@cmu.ac.th", "คณะวิศวกรรมศาสตร์", "CPE"],
    ]

    response = upload_xlsx(client, build_xlsx(VALID_HEADERS, rows))

    assert response.status_code == 201, response.text
    faculties = {s.student_id: s.faculty for s in db_session.query(Student).all()}
    assert faculties == {
        "640610001": "Faculty of Science",
        "640610002": "Faculty of Science",
        "640610003": "Faculty of Science",
        "640610004": "คณะวิศวกรรมศาสตร์",
    }


def test_legacy_xls_import_normalizes_faculty(client, db_session):
    content = build_legacy_xls(
        [
            [1, "670510670", "จักริน ชวชาติ", " คณะวิทยาศาสตร์ ", "10:05:00"],
            [2, "670510671", "สมหญิง ใจดี", "", "10:06:00"],
        ]
    )

    response = upload_legacy_xls(client, content)

    assert response.status_code == 201, response.text
    assert db_session.get(Student, "670510670").faculty == "Faculty of Science"
    assert db_session.get(Student, "670510671").faculty == "Faculty of Science"


# ------------------------------------------------------------
# POST /api/activities/{id}/participants/import/confirm
# ------------------------------------------------------------


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


def confirm(client, activity_id, students):
    return client.post(
        f"/api/activities/{activity_id}/participants/import/confirm",
        json={"students": students},
    )


def participant(student_id, faculty):
    return {
        "student_id": student_id,
        "first_name": "ชื่อ",
        "last_name": "นามสกุล",
        "email": "",
        "faculty": faculty,
    }


def test_participant_import_new_student_normalizes_faculty(client, db_session):
    activity = create_activity(db_session)

    response = confirm(
        client,
        activity.id,
        [
            participant("670510001", "คณะวิทยาศาสตร์"),
            participant("670510002", " faculty of science "),
            participant("670510003", ""),
        ],
    )

    assert response.status_code == 200, response.text
    db_session.expire_all()
    for student_id in ("670510001", "670510002", "670510003"):
        assert db_session.get(Student, student_id).faculty == "Faculty of Science"


def test_participant_import_existing_student_normalizes_faculty(client, db_session):
    activity = create_activity(db_session)
    db_session.add(
        Student(
            student_id="670510001",
            first_name="ชื่อ",
            last_name="นามสกุล",
            email="",
            faculty="คณะวิศวกรรมศาสตร์",
            major="",
        )
    )
    db_session.commit()

    response = confirm(client, activity.id, [participant("670510001", " คณะวิทยาศาสตร์")])

    assert response.status_code == 200, response.text
    db_session.expire_all()
    assert db_session.get(Student, "670510001").faculty == "Faculty of Science"


def test_participant_import_blank_faculty_keeps_existing_value(client, db_session):
    # คณะว่างในไฟล์ = "ไม่รู้" ไม่ใช่ "เปลี่ยนเป็นค่าเริ่มต้น" (เหมือน email / major)
    activity = create_activity(db_session)
    db_session.add(
        Student(
            student_id="670510001",
            first_name="ชื่อ",
            last_name="นามสกุล",
            email="",
            faculty="คณะวิศวกรรมศาสตร์",
            major="",
        )
    )
    db_session.commit()

    response = confirm(client, activity.id, [participant("670510001", "  ")])

    assert response.status_code == 200, response.text
    db_session.expire_all()
    assert db_session.get(Student, "670510001").faculty == "คณะวิศวกรรมศาสตร์"
