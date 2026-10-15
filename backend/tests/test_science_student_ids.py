"""รับเฉพาะนักศึกษาคณะวิทยาศาสตร์: รหัส 9 หลัก หลักที่ 3-5 = 051 ทุกช่องทางที่เพิ่มนักศึกษา"""

import pytest

from models import ActivityMember, Student
from student_ids import INVALID_STUDENT_ID_MESSAGE, is_science_student_id
from tests.test_participants_import_legacy_xls import confirm, create_activity, preview
from tests.test_settings_student_import import build_xlsx as build_settings_xlsx
from tests.test_settings_student_import import upload as upload_settings
from tests.test_students_import import VALID_HEADERS, build_xlsx
from tests.test_students_import import upload as upload_students
from tests.test_students_import_legacy_xls import build_legacy_xls
from tests.test_students_import_legacy_xls import upload as upload_legacy


SCIENCE = "670510001"
ENGINEERING = "670610001"


@pytest.mark.parametrize("value", ["670510001", "000510000", " 680519999 "])
def test_science_ids_are_valid(value):
    assert is_science_student_id(value)


@pytest.mark.parametrize(
    "value",
    ["670610001", "67051000", "6705100011", "67051000a", "S001", "", None, "６70510001", "๖๗๐๕๑๐๐๐๑"],
)
def test_other_faculties_and_bad_formats_are_invalid(value):
    assert not is_science_student_id(value)


def test_settings_import_rejects_other_faculty(client, db_session):
    rows = [[SCIENCE, "ก", "วิทย์", "", "เคมี"], [ENGINEERING, "ข", "วิศวะ", "", "เคมี"]]

    body = upload_settings(client, build_settings_xlsx(rows)).json()

    statuses = {row["student_id"]: (row["status"], row["message"]) for row in body["rows"]}
    assert statuses[ENGINEERING] == ("invalid", INVALID_STUDENT_ID_MESSAGE)
    assert (body["success"], body["failed"]) == (1, 1)
    assert db_session.get(Student, ENGINEERING) is None


def test_students_import_rejects_other_faculty(client, db_session):
    rows = [[SCIENCE, "A", "B", "a@cmu.ac.th", "", ""], [ENGINEERING, "C", "D", "c@cmu.ac.th", "", ""]]

    body = upload_students(client, build_xlsx(VALID_HEADERS, rows)).json()

    assert body["success_count"] == 1
    assert INVALID_STUDENT_ID_MESSAGE in body["failed_rows"][0]["errors"]
    assert db_session.get(Student, ENGINEERING) is None


def test_legacy_xls_import_rejects_other_faculty(client, db_session):
    content = build_legacy_xls([[1, SCIENCE, "ก วิทย์", "", "10:00:00"], [2, ENGINEERING, "ข วิศวะ", "", "10:01:00"]])

    body = upload_legacy(client, content).json()

    assert body["success"] == 1
    assert body["errors"][0]["reason"] == INVALID_STUDENT_ID_MESSAGE
    assert db_session.get(Student, ENGINEERING) is None


def test_participant_preview_flags_other_faculty(client, db_session):
    activity = create_activity(db_session)
    content = build_legacy_xls([[1, ENGINEERING, "ข วิศวะ", "", "10:01:00"]])

    body = preview(client, activity.id, content).json()

    assert body["invalid_count"] == 1
    assert INVALID_STUDENT_ID_MESSAGE in body["invalid_rows"][0]["errors"]


def test_participant_confirm_rejects_other_faculty_and_saves_nothing(client, db_session):
    activity = create_activity(db_session)
    student = {"first_name": "ก", "last_name": "ข", "email": "", "faculty": "", "major": "", "role": "participant"}

    response = confirm(client, activity.id, [
        {**student, "student_id": SCIENCE},
        {**student, "student_id": ENGINEERING},
    ])

    assert response.status_code == 400
    assert ENGINEERING in response.json()["detail"]
    assert db_session.query(Student).count() == 0
    assert db_session.query(ActivityMember).count() == 0
