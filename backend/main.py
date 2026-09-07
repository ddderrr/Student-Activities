from io import BytesIO
from pathlib import Path
import unicodedata

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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


# ============================================================
# TEST STORAGE ONLY
# ข้อมูลส่วนนี้อยู่แค่ใน RAM และจะหายเมื่อ restart backend
# ภายหลังเปลี่ยนเป็น PostgreSQL
# ============================================================

activity_participants: dict[int, dict[str, dict]] = {}


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

COLUMN_ALIASES = {
    "รหัสนักศึกษา": "student_id",
    "รหัสนักศึกษษา": "student_id",
    "Student ID": "student_id",
    "student_id": "student_id",

    "ชื่อ": "first_name",
    "First Name": "first_name",
    "first_name": "first_name",

    "นามสกุล": "last_name",
    "Last Name": "last_name",
    "last_name": "last_name",

    "CMU Email": "email",
    "อีเมล": "email",
    "Email": "email",
    "email": "email",

    # optional
    "สาขาวิชา": "major",
    "Major": "major",
    "major": "major",
}


def normalize_text(text: str) -> str:
    text = str(text)
    text = text.replace("\ufeff", "")
    text = text.replace("\u200b", "")
    text = text.strip()

    return unicodedata.normalize("NFC", text)


def normalize_student_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        normalize_text(column)
        for column in df.columns
    ]

    normalized_aliases = {
        normalize_text(key): value
        for key, value in COLUMN_ALIASES.items()
    }

    rename_map = {}

    for column in df.columns:
        normalized_column = normalize_text(column)

        if normalized_column in normalized_aliases:
            rename_map[column] = normalized_aliases[normalized_column]

    df = df.rename(columns=rename_map)

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

    keep_columns = required_columns.copy()

    if "major" in df.columns:
        keep_columns.append("major")

    df = df[keep_columns].copy()
    df = df.fillna("")

    for column in keep_columns:
        df[column] = df[column].astype(str).str.strip()

    return df


def validate_students(df: pd.DataFrame) -> list[dict]:
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
                    "row": int(index) + 2,
                    "errors": errors,
                }
            )

    return invalid_rows


async def read_student_file(file: UploadFile) -> dict:
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


# ============================================================
# IMPORT STUDENTS INTO A SPECIFIC ACTIVITY
# ============================================================

@app.post(
    "/api/activities/{activity_id}/participants/import/preview"
)
async def preview_activity_participants(
    activity_id: int,
    file: UploadFile = File(...),
):
    result = await read_student_file(file)

    return {
        "activity_id": activity_id,
        **result,
    }


class ConfirmImportRequest(BaseModel):
    students: list[dict]


@app.post(
    "/api/activities/{activity_id}/participants/import/confirm"
)
def confirm_activity_participants(
    activity_id: int,
    payload: ConfirmImportRequest,
):
    """
    TEST ONLY:
    เก็บ participant แยกตาม activity_id ใน memory

    activity 1 -> student A, B
    activity 2 -> student A, C

    นักศึกษาคนเดียวสามารถอยู่หลายกิจกรรมได้
    """

    if activity_id not in activity_participants:
        activity_participants[activity_id] = {}

    participants = activity_participants[activity_id]

    imported_count = 0
    duplicate_count = 0

    for student in payload.students:
        student_id = str(
            student.get("student_id", "")
        ).strip()

        if not student_id:
            raise HTTPException(
                status_code=400,
                detail="พบข้อมูลที่ไม่มี student_id",
            )

        if student_id in participants:
            duplicate_count += 1
            continue

        participants[student_id] = student
        imported_count += 1

    return {
        "activity_id": activity_id,
        "imported_count": imported_count,
        "duplicate_count": duplicate_count,
        "total_participants": len(participants),
    }


@app.get("/api/activities/{activity_id}/participants")
def get_activity_participants(activity_id: int):
    participants = activity_participants.get(
        activity_id,
        {},
    )

    return {
        "activity_id": activity_id,
        "total": len(participants),
        "students": list(participants.values()),
    }


