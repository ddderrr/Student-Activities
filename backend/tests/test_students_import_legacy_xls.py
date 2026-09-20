from io import BytesIO

import xlwt

from models import Student


XLS_CONTENT_TYPE = "application/vnd.ms-excel"

LEGACY_HEADERS = [
    "ลำดับ",
    "รหัสนักศึกษา",
    "ชื่อ",
    "คณะ",
    "เวลา",
]

META_ROWS = [
    ["Activity Code: ABC123"],
    ["Activity Name: Test Activity"],
    ["Timestamp: 2026-09-20 10:00:00"],
    ["Count: 0"],
]


def build_legacy_xls(rows, headers=LEGACY_HEADERS):
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Sheet1")

    for row_index, meta_row in enumerate(META_ROWS):
        for col_index, value in enumerate(meta_row):
            sheet.write(row_index, col_index, value)

    header_row_index = len(META_ROWS)

    for col_index, header in enumerate(headers):
        sheet.write(header_row_index, col_index, header)

    for offset, row in enumerate(rows):
        for col_index, value in enumerate(row):
            sheet.write(header_row_index + 1 + offset, col_index, value)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def upload(client, content, filename="checkin.xls", content_type=XLS_CONTENT_TYPE):
    return client.post(
        "/api/students/import",
        files={"file": (filename, content, content_type)},
    )


def test_import_valid_legacy_xls_creates_students(client, db_session):
    content = build_legacy_xls(
        [
            [1, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"],
            [2, "670510671", "สมหญิง ใจดี", "คณะวิทยาศาสตร์", "10:06:00"],
        ]
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 2
    assert body["success"] == 2
    assert body["skipped"] == 0
    assert body["errors"] == []
    assert body["warnings"] == []

    saved = (
        db_session.query(Student)
        .order_by(Student.student_id)
        .all()
    )
    assert [s.student_id for s in saved] == [
        "670510670",
        "670510671",
    ]
    assert saved[0].first_name == "จักริน"
    assert saved[0].last_name == "ชวชาติ"
    assert saved[0].faculty == "คณะวิทยาศาสตร์"
    assert saved[0].email == ""


def test_import_rejects_wrong_format(client):
    response = upload(
        client,
        b"student_id,full_name\n1,a",
        filename="checkin.csv",
        content_type="text/csv",
    )

    assert response.status_code == 400
    assert "xls" in response.json()["detail"]


def test_import_rejects_corrupt_xls_content(client):
    response = upload(client, b"this is not a real xls file")

    assert response.status_code == 400
    assert "ไม่สามารถอ่านไฟล์ได้" in response.json()["detail"]


def test_import_rejects_missing_required_columns(client):
    content = build_legacy_xls(
        [[1, "670510670", "จักริน ชวชาติ", "10:05:00"]],
        headers=["ลำดับ", "รหัสนักศึกษา", "ชื่อ", "เวลา"],
    )

    response = upload(client, content)

    assert response.status_code == 400
    assert "faculty" in response.json()["detail"]


def test_import_skips_duplicate_student_id_within_file(client, db_session):
    content = build_legacy_xls(
        [
            [1, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"],
            [2, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:07:00"],
        ]
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 2
    assert body["success"] == 1
    assert body["skipped"] == 1
    assert body["errors"] == []
    assert len(body["warnings"]) == 1
    assert "ซ้ำในไฟล์" in body["warnings"][0]["reason"]

    assert db_session.query(Student).count() == 1


def test_import_skips_student_id_already_in_database(client, db_session):
    db_session.add(
        Student(
            student_id="670510670",
            first_name="Existing",
            last_name="Student",
            email="existing@cmu.ac.th",
            faculty="Faculty of Science",
            major="",
        )
    )
    db_session.commit()

    content = build_legacy_xls(
        [[1, "670510670", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"]]
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] == 0
    assert body["skipped"] == 1
    assert "ในระบบแล้ว" in body["warnings"][0]["reason"]

    student = db_session.get(Student, "670510670")
    assert student.first_name == "Existing"


def test_import_reports_empty_student_id_as_error(client, db_session):
    content = build_legacy_xls(
        [
            [1, "", "จักริน ชวชาติ", "คณะวิทยาศาสตร์", "10:05:00"],
            [2, "670510671", "สมหญิง ใจดี", "คณะวิทยาศาสตร์", "10:06:00"],
        ]
    )

    response = upload(client, content)

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 2
    assert body["success"] == 1
    assert body["skipped"] == 0
    assert len(body["errors"]) == 1
    assert "ไม่มีรหัสนักศึกษา" in body["errors"][0]["reason"]

    assert db_session.query(Student).count() == 1
