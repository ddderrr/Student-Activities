from io import BytesIO

import openpyxl

from models import Student
from tests.conftest import CHEM_ADMIN_EMAIL


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
THAI_HEADERS = ["รหัสนักศึกษา", "ชื่อ", "นามสกุล", "อีเมล", "สาขาวิชา"]


def build_xlsx(rows, headers=THAI_HEADERS):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def upload(client, content, dry_run=False, filename="students.xlsx", headers=None):
    return client.post(
        "/api/admin/students/import",
        params={"dry_run": "true"} if dry_run else None,
        files={"file": (filename, content, XLSX)},
        headers=headers,
    )


def make_student(db_session, student_id):
    db_session.add(
        Student(
            student_id=student_id,
            first_name="เดิม",
            last_name="อยู่แล้ว",
            email="old@test.com",
            faculty="คณะวิทยาศาสตร์",
            major="เคมี",
        )
    )
    db_session.commit()


VALID_ROWS = [
    ["680510001", "สมชาย", "ใจดี", "somchai@cmu.ac.th", "เคมี"],
    ["680510002", "สมหญิง", "รักเรียน", "", "วิทยาการคอมพิวเตอร์"],
]


def test_preview_does_not_insert_and_reports_each_row(client, db_session):
    response = upload(client, build_xlsx(VALID_ROWS), dry_run=True)

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert (body["total"], body["success"], body["skipped"], body["failed"]) == (2, 2, 0, 0)
    assert [row["status"] for row in body["rows"]] == ["new", "new"]
    assert body["rows"][0]["first_name"] == "สมชาย"
    assert body["rows"][1]["email"] == ""  # ช่องว่างต้องเป็น "" ไม่ใช่ "nan"
    assert db_session.query(Student).count() == 0


def test_confirm_inserts_new_students(client, db_session):
    response = upload(client, build_xlsx(VALID_ROWS))

    assert response.status_code == 200
    assert response.json()["success"] == 2
    student = db_session.get(Student, "680510001")
    assert (student.first_name, student.last_name, student.email, student.major) == (
        "สมชาย", "ใจดี", "somchai@cmu.ac.th", "เคมี",
    )


def test_duplicates_are_skipped_not_errors(client, db_session):
    make_student(db_session, "680510001")
    rows = VALID_ROWS + [["680510002", "ซ้ำ", "ในไฟล์", "", "เคมี"]]

    response = upload(client, build_xlsx(rows))

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["success"], body["skipped"], body["failed"]) == (3, 1, 2, 0)
    messages = {(error["student_id"], error["type"], error["message"]) for error in body["errors"]}
    assert ("680510001", "duplicate", "มีรหัสนักศึกษานี้ในระบบแล้ว") in messages
    assert ("680510002", "duplicate", "รหัสนักศึกษาซ้ำในไฟล์") in messages
    # ข้อมูลเดิมไม่ถูกเขียนทับ และแถวแรกของรหัสที่ซ้ำในไฟล์ถูกนำเข้า
    db_session.expire_all()
    assert db_session.get(Student, "680510001").first_name == "เดิม"
    assert db_session.get(Student, "680510002").first_name == "สมหญิง"


def test_invalid_rows_are_counted_as_failed(client, db_session):
    rows = [
        ["", "ไม่มี", "รหัส", "", "เคมี"],
        ["680510003", "", "ไม่มีชื่อ", "", "เคมี"],
        ["680510004", "อีเมล", "ผิด", "not-an-email", "เคมี"],
        ["6" * 31, "รหัส", "ยาวเกิน", "", "เคมี"],
        ["680510005", "ถูก", "ต้อง", "", "เคมี"],
    ]

    body = upload(client, build_xlsx(rows)).json()

    assert (body["total"], body["success"], body["skipped"], body["failed"]) == (5, 1, 0, 4)
    by_row = {error["row"]: error["message"] for error in body["errors"]}
    assert by_row[2] == "ไม่มีรหัสนักศึกษา"
    assert "ไม่มีชื่อ" in by_row[3]
    assert "รูปแบบอีเมลไม่ถูกต้อง" in by_row[4]
    assert "ยาวเกิน" in by_row[5]
    assert db_session.query(Student).count() == 1


def test_numeric_ids_and_blank_rows(client, db_session):
    # รหัสที่ Excel เก็บเป็นตัวเลข + แถวว่างท้ายไฟล์
    body = upload(client, build_xlsx([[680510006, "ตัว", "เลข", None, "เคมี"], [None] * 5])).json()

    assert body["total"] == 1
    assert body["rows"][0]["student_id"] == "680510006"


def test_english_headers_are_accepted(client):
    headers = ["student_id", "first_name", "last_name", "email", "major"]
    body = upload(client, build_xlsx(VALID_ROWS, headers=headers), dry_run=True).json()

    assert body["success"] == 2


def test_missing_student_id_column_returns_400(client):
    response = upload(client, build_xlsx([["สมชาย", "ใจดี"]], headers=["ชื่อ", "นามสกุล"]))

    assert response.status_code == 400
    assert "รหัสนักศึกษา" in response.json()["detail"]


def test_rejects_other_file_types(client):
    response = upload(client, b"a,b", filename="students.txt")

    assert response.status_code == 400


CSV_TEXT = (
    "รหัสนักศึกษา,ชื่อ,นามสกุล,อีเมล,สาขาวิชา\n"
    "680510001,สมชาย,ใจดี,somchai@cmu.ac.th,เคมี\n"
    "0680510002,สมหญิง,รักเรียน,,วิทยาการคอมพิวเตอร์\n"
    "\n"
)


def test_csv_utf8_with_bom_imports(client, db_session):
    response = upload(client, CSV_TEXT.encode("utf-8-sig"), filename="students.csv")

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["success"]) == (2, 2)
    assert body["rows"][1]["email"] == ""
    # CSV ไม่ตัดเลขศูนย์นำหน้า
    assert db_session.get(Student, "0680510002").first_name == "สมหญิง"


def test_csv_windows_thai_encoding_and_semicolon(client):
    content = CSV_TEXT.replace(",", ";").encode("cp874")

    body = upload(client, content, dry_run=True, filename="students.CSV").json()

    assert body["success"] == 2
    assert body["rows"][0]["first_name"] == "สมชาย"
    assert body["rows"][0]["major"] == "เคมี"


def test_csv_duplicates_skipped_like_excel(client, db_session):
    make_student(db_session, "680510001")

    body = upload(client, CSV_TEXT.encode("utf-8"), filename="students.csv").json()

    assert (body["success"], body["skipped"]) == (1, 1)


def test_branch_admin_gets_403(client, db_session):
    branch = {"X-Admin-Email": CHEM_ADMIN_EMAIL}

    assert upload(client, build_xlsx(VALID_ROWS), headers=branch).status_code == 403
    assert client.get("/api/admin/students/import/template", headers=branch).status_code == 403
    assert db_session.query(Student).count() == 0


def test_template_has_thai_headers(client):
    response = client.get("/api/admin/students/import/template")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    sheet = openpyxl.load_workbook(BytesIO(response.content)).active
    assert [cell.value for cell in sheet[1]] == THAI_HEADERS
    # ไฟล์ template นำเข้ากลับได้ทันที (มีแค่หัวคอลัมน์ = 0 แถว)
    assert upload(client, response.content, dry_run=True).json()["total"] == 0
