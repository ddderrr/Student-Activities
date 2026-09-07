from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


@app.get("/")
def home():
    return {"message": "Hello"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ชื่อ column จาก Google Forms / Excel -> ชื่อมาตรฐานที่ frontend ใช้
COLUMN_ALIASES = {
    "รหัสนักศึกษา": "student_id",
    "Student ID": "student_id",
    "student_id": "student_id",

    "ชื่อ": "first_name",
    "First Name": "first_name",
    "first_name": "first_name",

    "นามสกุล": "last_name",
    "Last Name": "last_name",
    "last_name": "last_name",

    "CMU Email": "email",
    "Email": "email",
    "email": "email",
}


def normalize_student_columns(df: pd.DataFrame) -> pd.DataFrame:

    # ทำความสะอาดชื่อ column
    df.columns = [
        str(column)
        .replace("\ufeff", "")
        .replace("\u200b", "")
        .strip()
        for column in df.columns
    ]

    print("CSV columns:", df.columns.tolist())

    column_aliases = {
        "รหัสนักศึกษา": "student_id",
        "รหัสนักศึกษษา" : "student_id",
        "student_id": "student_id",
        "Student ID": "student_id",

        "ชื่อ": "first_name",
        "first_name": "first_name",
        "First Name": "first_name",

        "นามสกุล": "last_name",
        "last_name": "last_name",
        "Last Name": "last_name",

        "CMU Email": "email",
        "อีเมล": "email",
        "Email": "email",
        "email": "email",
    }

    df = df.rename(columns=column_aliases)

    print("After rename:", df.columns.tolist())

    required_columns = [
        "student_id",
        "first_name",
        "last_name",
        "email",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=(
                "ไม่พบ column ที่จำเป็น: "
                + ", ".join(missing_columns)
                + f" | column ที่พบ: {list(df.columns)}"
            ),
        )

    df = df[required_columns].copy()

    df = df.fillna("")

    for column in required_columns:
        df[column] = df[column].astype(str).str.strip()

    return df   


def validate_students(df: pd.DataFrame) -> list[dict]:
    """
    Validation เบื้องต้นสำหรับหน้า Preview
    ยังไม่มีการบันทึกลง PostgreSQL
    """

    invalid_rows = []

    for index, row in df.iterrows():
        errors = []

        if not row["student_id"]:
            errors.append("ไม่มีรหัสนักศึกษา")

        if not row["first_name"]:
            errors.append("ไม่มีชื่อ")

        if not row["last_name"]:
            errors.append("ไม่มีนามสกุล")

        if not row["email"]:
            errors.append("ไม่มีอีเมล")
        elif "@" not in row["email"]:
            errors.append("รูปแบบอีเมลไม่ถูกต้อง")

        if errors:
            invalid_rows.append(
                {
                    # +2 เพราะ index เริ่ม 0 และแถวแรกของไฟล์เป็น header
                    "row": int(index) + 2,
                    "errors": errors,
                }
            )

    return invalid_rows


async def read_student_file(file: UploadFile) -> dict:
    """
    อ่าน CSV / Excel แล้วคืนข้อมูลสำหรับ Preview
    """

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=400,
            detail="รองรับเฉพาะไฟล์ .csv และ .xlsx",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="ไฟล์ว่าง",
        )

    try:
        if extension == ".csv":
            df = pd.read_csv(
                BytesIO(contents),
                dtype=str,
            )
        else:
            df = pd.read_excel(
                BytesIO(contents),
                dtype=str,
            )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"ไม่สามารถอ่านไฟล์ได้: {exc}",
        )

    df = normalize_student_columns(df)

    invalid_rows = validate_students(df)

    students = df.to_dict(orient="records")

    return {
        "filename": filename,
        "total": len(students),
        "columns": list(df.columns),
        "students": students,
        "invalid_count": len(invalid_rows),
        "invalid_rows": invalid_rows,
    }


# Endpoint ใหม่สำหรับหน้า Vue ที่ทำ Preview ก่อน Import จริง
@app.post("/api/students/import/preview")
async def preview_import_students(file: UploadFile = File(...)):
    return await read_student_file(file)


# เก็บ endpoint เดิมของคุณไว้ด้วย
# เพื่อให้ code เก่าที่ยิง POST /students/import ยังใช้ได้
@app.post("/students/import")
async def import_students(file: UploadFile = File(...)):
    return await read_student_file(file)


# ขั้นต่อไปค่อยทำ endpoint สำหรับบันทึกลง PostgreSQL จริง เช่น:
#
# @app.post("/api/students/import/confirm")
# async def confirm_import_students(...):
#     1. ตรวจข้อมูลอีกครั้ง
#     2. เช็ก student_id ซ้ำใน database
#     3. insert Student
#     4. insert ActivityRegistration
#     5. commit transaction
