"""จำกัดขนาดไฟล์ import (Excel / CSV) ก่อนให้ pandas อ่าน

ไฟล์ .xlsx เป็น zip: ไฟล์ขนาดไม่กี่ KB ที่มีข้อมูลแค่ช่อง A1 กับ XFD<N> ทำให้ pandas
สร้างตาราง N x 16,384 ช่อง (หลาย GB) และ CSV ที่หัวตารางกว้างมากทำให้ pandas
เติมทุกแถวให้กว้างเท่ากัน จึงตรวจขนาดไฟล์และจำนวนแถว / คอลัมน์ที่มีข้อมูลจริง
แบบ streaming ก่อน (ดู docs/security-review.md ข้อ ก4)
"""

import csv
import io
import zipfile

import openpyxl
import xlrd
from fastapi import HTTPException, UploadFile

MAX_IMPORT_BYTES = 5 * 1024 * 1024
# ไม่นับแถวหัวตาราง
MAX_IMPORT_ROWS = 20_000
MAX_IMPORT_COLUMNS = 50
# .xlsx ปกติแตกไฟล์แล้วใหญ่ขึ้นราว 5-10 เท่า
MAX_XLSX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
# แถวก่อนข้อมูลที่ยอมให้เกิน MAX_IMPORT_ROWS: หัวตาราง และแถว metadata ของไฟล์ .xls
# จากระบบเช็คชื่อรุ่นเก่า (ดู read_legacy_xls_dataframe)
HEADER_ROW_ALLOWANCE = 20

XLSX_MAGIC = b"PK\x03\x04"
XLS_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
CSV_ENCODINGS = ("utf-8-sig", "cp874")
CSV_DELIMITERS = (",", ";", "\t")


def read_import_upload(file: UploadFile) -> bytes:
    """อ่านไฟล์ไม่เกิน MAX_IMPORT_BYTES (ไม่อ่านทั้งไฟล์เข้าหน่วยความจำก่อนตรวจ)

    อ่านแบบ sync: endpoint import เป็น def ธรรมดา ให้ FastAPI รันใน thread แยก
    การอ่านไฟล์ด้วย pandas ซึ่งใช้เวลาหลายวินาทีจึงไม่บล็อก request อื่น
    """
    contents = file.file.read(MAX_IMPORT_BYTES + 1)

    if len(contents) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=400, detail="ไฟล์ใหญ่เกิน 5MB")

    return contents


def ensure_import_file_within_limits(contents: bytes, extension: str) -> None:
    """ตรวจตามเนื้อไฟล์จริง ไม่ใช่นามสกุล เพราะ pandas เลือกวิธีอ่านจากเนื้อไฟล์

    ไฟล์ที่อ่านไม่ออกปล่อยผ่าน ให้โค้ด import เดิมแจ้ง error ตามปกติ
    """
    if contents.startswith(XLSX_MAGIC):
        _check_xlsx(contents)
    elif contents.startswith(XLS_MAGIC):
        _check_xls(contents)
    elif extension == ".csv":
        _check_csv(contents)


def _reject_rows() -> None:
    raise HTTPException(
        status_code=400,
        detail=f"ไฟล์มีข้อมูลเกิน {MAX_IMPORT_ROWS:,} แถว",
    )


def _reject_columns() -> None:
    raise HTTPException(
        status_code=400,
        detail=f"ไฟล์มีข้อมูลเกิน {MAX_IMPORT_COLUMNS} คอลัมน์",
    )


def _check_dimensions(last_row: int, last_column: int) -> None:
    if last_column > MAX_IMPORT_COLUMNS:
        _reject_columns()
    if last_row > MAX_IMPORT_ROWS + HEADER_ROW_ALLOWANCE:
        _reject_rows()


def _last_filled_column(values) -> int:
    for index in range(len(values) - 1, -1, -1):
        if values[index] not in (None, ""):
            return index + 1
    return 0


def _check_xlsx(contents: bytes) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(contents))
    except zipfile.BadZipFile:
        return

    # zipfile อ่านแต่ละไฟล์ได้ไม่เกิน file_size ที่ประกาศไว้ จึงเชื่อค่านี้ได้
    if sum(info.file_size for info in archive.infolist()) > MAX_XLSX_UNCOMPRESSED_BYTES:
        raise HTTPException(status_code=400, detail="ไฟล์ใหญ่เกินไปเมื่อแตกไฟล์ออกมา")

    try:
        workbook = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
    except Exception:
        return

    try:
        sheet = workbook.worksheets[0]
        # ไม่เชื่อขนาดตาราง (<dimension>) ที่ไฟล์ประกาศเอง ให้อ่านเฉพาะช่องที่มีอยู่จริง
        sheet.reset_dimensions()
        last_row = 0
        last_column = 0

        for row_number, values in enumerate(sheet.iter_rows(values_only=True), start=1):
            filled = _last_filled_column(values)
            if filled:
                last_row = row_number
                last_column = max(last_column, filled)
                _check_dimensions(last_row, last_column)
            elif row_number > (MAX_IMPORT_ROWS + HEADER_ROW_ALLOWANCE) * 10:
                # แถวว่างจำนวนมาก: ไม่ต้องอ่านต่อจนจบไฟล์
                _reject_rows()
    finally:
        workbook.close()


def _check_xls(contents: bytes) -> None:
    try:
        workbook = xlrd.open_workbook(file_contents=contents, on_demand=True)
    except Exception:
        return

    try:
        sheet = workbook.sheet_by_index(0)
        last_row = 0
        last_column = 0

        for row_index in range(sheet.nrows):
            filled = _last_filled_column(sheet.row_values(row_index))
            if filled:
                last_row = row_index + 1
                last_column = max(last_column, filled)
                _check_dimensions(last_row, last_column)
    finally:
        workbook.release_resources()


def _check_csv(contents: bytes) -> None:
    for encoding in CSV_ENCODINGS:
        try:
            text = contents.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return

    # ตรวจทุกตัวคั่นที่ pandas อาจเลือก (หน้า Settings ให้ pandas เดาตัวคั่นเอง)
    for delimiter in CSV_DELIMITERS:
        rows = 0
        try:
            for values in csv.reader(io.StringIO(text), delimiter=delimiter):
                if len(values) > MAX_IMPORT_COLUMNS:
                    _reject_columns()
                if any(values):
                    rows += 1
                    if rows > MAX_IMPORT_ROWS + 1:
                        _reject_rows()
        except csv.Error:
            # เช่น ช่องเดียวยาวเกิน csv.field_size_limit() (128 KB)
            raise HTTPException(status_code=400, detail="ไม่สามารถอ่านไฟล์ได้")
