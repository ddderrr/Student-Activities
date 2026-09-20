from io import BytesIO

import openpyxl

from models import Student


XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

VALID_HEADERS = [
    "student_id",
    "first_name",
    "last_name",
    "email",
    "faculty",
    "major",
]


def build_xlsx(headers, rows):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(headers)

    for row in rows:
        sheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def upload(client, content, filename="students.xlsx", content_type=XLSX_CONTENT_TYPE):
    return client.post(
        "/api/students/import",
        files={"file": (filename, content, content_type)},
    )


def test_import_valid_file_creates_students(client, db_session):
    content = build_xlsx(
        VALID_HEADERS,
        [
            [
                "640610001",
                "Somchai",
                "Jaidee",
                "somchai_j@cmu.ac.th",
                "Faculty of Science",
                "CS",
            ],
            [
                "640610002",
                "Somsri",
                "Jaidee",
                "somsri_j@cmu.ac.th",
                "Faculty of Science",
                "IT",
            ],
        ],
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 2
    assert body["success_count"] == 2
    assert body["failed_count"] == 0
    assert body["failed_rows"] == []

    saved = (
        db_session.query(Student)
        .order_by(Student.student_id)
        .all()
    )
    assert [s.student_id for s in saved] == [
        "640610001",
        "640610002",
    ]
    assert saved[0].first_name == "Somchai"
    assert saved[0].major == "CS"


def test_import_rejects_non_xlsx_extension(client):
    response = upload(
        client,
        b"student_id,first_name\n1,a",
        filename="students.csv",
        content_type="text/csv",
    )

    assert response.status_code == 400
    assert "xlsx" in response.json()["detail"]


def test_import_rejects_corrupt_xlsx_content(client):
    response = upload(client, b"this is not a real xlsx file")

    assert response.status_code == 400
    assert "ไม่สามารถอ่านไฟล์ได้" in response.json()["detail"]


def test_import_rejects_missing_required_columns(client):
    content = build_xlsx(
        ["student_id", "first_name"],
        [["640610003", "Somchai"]],
    )

    response = upload(client, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "last_name" in detail
    assert "email" in detail


def test_import_reports_duplicate_within_file(client, db_session):
    content = build_xlsx(
        VALID_HEADERS,
        [
            ["640610004", "A", "B", "a@cmu.ac.th", "", ""],
            ["640610004", "C", "D", "c@cmu.ac.th", "", ""],
        ],
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["success_count"] == 0
    assert body["failed_count"] == 2
    assert all(
        "รหัสนักศึกษาซ้ำในไฟล์" in row["errors"]
        for row in body["failed_rows"]
    )
    assert db_session.query(Student).count() == 0


def test_import_reports_duplicate_already_in_database(client, db_session):
    db_session.add(
        Student(
            student_id="640610005",
            first_name="Existing",
            last_name="Student",
            email="existing@cmu.ac.th",
            faculty="Faculty of Science",
            major="",
        )
    )
    db_session.commit()

    content = build_xlsx(
        VALID_HEADERS,
        [["640610005", "New", "Name", "new@cmu.ac.th", "", ""]],
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    assert (
        "มีรหัสนักศึกษานี้ในระบบแล้ว"
        in body["failed_rows"][0]["errors"]
    )

    student = db_session.get(Student, "640610005")
    assert student.first_name == "Existing"


def test_import_skips_invalid_rows_but_saves_valid_ones(
    client,
    db_session,
):
    content = build_xlsx(
        VALID_HEADERS,
        [
            [
                "640610006",
                "Valid",
                "Row",
                "valid@cmu.ac.th",
                "",
                "",
            ],
            ["", "NoId", "Row", "noid@cmu.ac.th", "", ""],
            [
                "640610007",
                "",
                "MissingFirst",
                "missingfirst@cmu.ac.th",
                "",
                "",
            ],
            [
                "640610008",
                "BadEmail",
                "Row",
                "not-an-email",
                "",
                "",
            ],
        ],
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 4
    assert body["success_count"] == 1
    assert body["failed_count"] == 3

    saved_ids = {
        s.student_id for s in db_session.query(Student).all()
    }
    assert saved_ids == {"640610006"}
