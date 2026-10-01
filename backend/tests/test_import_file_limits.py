"""จำกัดขนาดไฟล์ import ทุกหน้า: 5MB / 20,000 แถว / 50 คอลัมน์

ไฟล์ .xlsx เป็น zip: ไฟล์ขนาดไม่กี่ KB ที่มีข้อมูลแค่ช่อง A1 กับ XFD<N> ทำให้ pandas
สร้างตาราง N x 16,384 ช่อง ใช้หน่วยความจำหลาย GB และเซิร์ฟเวอร์ค้าง จึงต้องตรวจ
ขนาดจริงก่อนให้ pandas อ่าน (ดู docs/security-review.md ข้อ ก4)

หน้า import ที่ครอบคลุม
- POST /api/activities/{id}/participants/import/preview (.csv / .xlsx / .xls)
- POST /api/activities/{id}/participants/import/confirm (จำนวนแถวที่ส่งมา)
- POST /api/students/import (.xlsx / .xls)
- POST /api/admin/students/import (หน้า Settings: .csv / .xlsx / .xls)
"""

import zipfile
from datetime import datetime
from io import BytesIO

import openpyxl
import pytest
import xlwt

from import_limits import MAX_IMPORT_COLUMNS, MAX_IMPORT_ROWS
from models import Activity

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
XLS = "application/vnd.ms-excel"
HEADERS = ["student_id", "first_name", "last_name", "email"]


def xlsx_bytes(cells: dict[tuple[int, int], str]) -> bytes:
    """cells: {(row, column): value} เขียนเฉพาะช่องที่ระบุ (ไฟล์เล็กแม้ช่องจะอยู่ไกล)"""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for column, header in enumerate(HEADERS, 1):
        sheet.cell(row=1, column=column, value=header)
    for (row, column), value in cells.items():
        sheet.cell(row=row, column=column, value=value)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def valid_row(row):
    return {(row, 1): f"6705{row:05d}", (row, 2): "A", (row, 3): "B", (row, 4): f"{row}@cmu.ac.th"}


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


@pytest.fixture()
def upload(client, db_session):
    """upload(path_key, filename, content) ไปยังหน้า import ที่เลือก"""
    activity = create_activity(db_session)
    urls = {
        "preview": f"/api/activities/{activity.id}/participants/import/preview",
        "students": "/api/students/import",
        "settings": "/api/admin/students/import?dry_run=true",
    }

    def _upload(page, filename, content):
        content_type = XLS if filename.endswith(".xls") else XLSX
        return client.post(urls[page], files={"file": (filename, content, content_type)})

    return _upload


XLSX_PAGES = ["preview", "students", "settings"]


# ------------------------------------------------------------
# .xlsx
# ------------------------------------------------------------


@pytest.mark.parametrize("page", XLSX_PAGES)
def test_xlsx_sparse_bomb_is_rejected(upload, page):
    # ข้อมูลแค่ 3 ช่อง แต่ pandas จะสร้างตาราง 30,000 x 16,384 ช่อง
    content = xlsx_bytes({(1, 16384): "z", (30000, 1): "1"})
    assert len(content) < 10_000

    response = upload(page, "students.xlsx", content)

    assert response.status_code == 400
    assert "คอลัมน์" in response.json()["detail"]


@pytest.mark.parametrize("page", XLSX_PAGES)
def test_xlsx_too_many_columns_is_rejected(upload, page):
    response = upload(page, "students.xlsx", xlsx_bytes({(2, MAX_IMPORT_COLUMNS + 1): "x"}))

    assert response.status_code == 400
    assert f"{MAX_IMPORT_COLUMNS}" in response.json()["detail"]


@pytest.mark.parametrize("page", XLSX_PAGES)
def test_xlsx_too_many_rows_is_rejected(upload, page):
    response = upload(page, "students.xlsx", xlsx_bytes(valid_row(MAX_IMPORT_ROWS + 30)))

    assert response.status_code == 400
    assert f"{MAX_IMPORT_ROWS:,}" in response.json()["detail"]


@pytest.mark.parametrize("page", XLSX_PAGES)
def test_xlsx_huge_when_uncompressed_is_rejected(upload, page):
    buffer = BytesIO(xlsx_bytes(valid_row(2)))
    with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED) as archive:
        # 200 MB ของ 0 บีบอัดเหลือไม่กี่ร้อย KB
        archive.writestr("xl/media/padding.bin", b"\0" * (200 * 1024 * 1024))
    content = buffer.getvalue()
    assert len(content) < 1024 * 1024

    response = upload(page, "students.xlsx", content)

    assert response.status_code == 400
    assert "แตกไฟล์" in response.json()["detail"]


@pytest.mark.parametrize("page", ["preview", "students"])
def test_file_over_5mb_is_rejected(upload, page):
    content = b"PK" + b"\0" * (5 * 1024 * 1024)

    response = upload(page, "students.xlsx", content)

    assert response.status_code == 400
    assert "5MB" in response.json()["detail"]


def test_preview_accepts_file_at_row_limit(upload):
    cells = {}
    for row in range(2, MAX_IMPORT_ROWS + 2):
        cells.update(valid_row(row))

    response = upload("preview", "students.xlsx", xlsx_bytes(cells))

    assert response.status_code == 200, response.text
    assert response.json()["total"] == MAX_IMPORT_ROWS


# ------------------------------------------------------------
# .xls (ไฟล์เช็คอินระบบเก่า และ .xls ทั่วไปในหน้า Settings)
# ------------------------------------------------------------


def xls_bytes(cells: dict[tuple[int, int], str]) -> bytes:
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Sheet1")
    for column, header in enumerate(["ลำดับ", "รหัสนักศึกษา", "ชื่อ", "คณะ", "เวลา"]):
        sheet.write(0, column, header)
    for (row, column), value in cells.items():
        sheet.write(row - 1, column - 1, value)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


@pytest.mark.parametrize("page", XLSX_PAGES)
def test_xls_too_many_columns_is_rejected(upload, page):
    response = upload(page, "checkin.xls", xls_bytes({(2, MAX_IMPORT_COLUMNS + 1): "x"}))

    assert response.status_code == 400
    assert f"{MAX_IMPORT_COLUMNS}" in response.json()["detail"]


@pytest.mark.parametrize("page", XLSX_PAGES)
def test_xls_too_many_rows_is_rejected(upload, page):
    response = upload(page, "checkin.xls", xls_bytes({(MAX_IMPORT_ROWS + 30, 2): "670510001"}))

    assert response.status_code == 400
    assert f"{MAX_IMPORT_ROWS:,}" in response.json()["detail"]


# ------------------------------------------------------------
# .csv
# ------------------------------------------------------------


@pytest.fixture()
def upload_csv(client, db_session):
    activity = create_activity(db_session)
    urls = {
        "preview": f"/api/activities/{activity.id}/participants/import/preview",
        "settings": "/api/admin/students/import?dry_run=true",
    }

    def _upload(page, text):
        return client.post(urls[page], files={"file": ("students.csv", text.encode(), "text/csv")})

    return _upload


@pytest.mark.parametrize("page", ["preview", "settings"])
def test_csv_wide_header_bomb_is_rejected(upload_csv, page):
    # หัวตารางกว้าง 100,000 คอลัมน์ + แถวว่างจำนวนมาก: pandas เติมทุกแถวให้กว้างเท่าหัวตาราง
    text = ",".join(HEADERS) + "," * 100_000 + "\n" + "x\n" * 1000

    response = upload_csv(page, text)

    assert response.status_code == 400
    assert f"{MAX_IMPORT_COLUMNS}" in response.json()["detail"]


@pytest.mark.parametrize("page", ["preview", "settings"])
def test_csv_too_many_rows_is_rejected(upload_csv, page):
    text = ",".join(HEADERS) + "\n" + "670510001,A,B,a@cmu.ac.th\n" * (MAX_IMPORT_ROWS + 1)

    response = upload_csv(page, text)

    assert response.status_code == 400
    assert f"{MAX_IMPORT_ROWS:,}" in response.json()["detail"]


def test_csv_quoted_commas_are_not_counted_as_columns(upload_csv):
    text = ",".join(HEADERS) + "\n" + '670510001,"A' + "," * 100 + '",B,a@cmu.ac.th\n'

    response = upload_csv("preview", text)

    assert response.status_code == 200, response.text


# ------------------------------------------------------------
# confirm: จำนวนแถวที่ส่งมาใน JSON
# ------------------------------------------------------------


def test_confirm_rejects_too_many_rows(client, db_session):
    activity = create_activity(db_session)
    rows = [
        {"student_id": f"6705{index:05d}", "first_name": "A", "last_name": "B"}
        for index in range(MAX_IMPORT_ROWS + 1)
    ]

    response = client.post(
        f"/api/activities/{activity.id}/participants/import/confirm",
        json={"students": rows},
    )

    assert response.status_code == 422
