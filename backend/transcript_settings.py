"""หัวเอกสาร Transcript ที่แอดมินกลางแก้ได้จากหน้า Settings (เก็บใน app_settings)

แต่ละช่องมีทั้งภาษาไทยและอังกฤษ (PDF ออกได้สองภาษา) ช่องที่ไม่ได้ตั้ง / ลบให้ว่าง
= ใช้ค่าเริ่มต้นจาก transcript_config.py มีผลกับ PDF ที่สร้างหลังบันทึกทันที
"""

from sqlalchemy.orm import Session

import transcript_config
from models import AppSetting

KEY_PREFIX = "transcript."
MAX_LENGTH = 200

# field -> ค่าเริ่มต้น
DEFAULTS = {
    "university_name": transcript_config.UNIVERSITY_NAME,
    "university_name_en": transcript_config.UNIVERSITY_NAME_EN,
    "faculty_name": transcript_config.FACULTY_NAME,
    "faculty_name_en": transcript_config.FACULTY_SHORT_NAME_EN,
    "document_title": transcript_config.DOCUMENT_TITLE,
    "document_title_en": transcript_config.DOCUMENT_TITLE_EN,
    "signer_name": transcript_config.SIGNER_NAME,
    "signer_name_en": transcript_config.SIGNER_NAME_EN,
    "signer_position": transcript_config.SIGNER_POSITION,
    "signer_position_en": transcript_config.SIGNER_POSITION_EN,
}
FIELDS = tuple(DEFAULTS)


def load_overrides(db: Session) -> dict[str, str]:
    """เฉพาะช่องที่แอดมินตั้งไว้"""
    rows = db.query(AppSetting).filter(AppSetting.key.like(f"{KEY_PREFIX}%")).all()
    values = {row.key[len(KEY_PREFIX):]: row.value for row in rows}
    return {field: values[field] for field in FIELDS if values.get(field)}


def load_header(db: Session) -> dict[str, str]:
    """ค่าที่ใช้จริงทุกช่อง (ค่าที่ตั้ง หรือค่าเริ่มต้น)"""
    return {**DEFAULTS, **load_overrides(db)}


def clean_value(field: str, raw) -> str:
    value = " ".join(str(raw or "").split())
    if len(value) > MAX_LENGTH:
        raise ValueError(f"{field} ยาวเกิน {MAX_LENGTH} ตัวอักษร")
    return value


def preview_header(db: Session, values: dict) -> dict[str, str]:
    """ค่าที่จะใช้ถ้าบันทึก values (ยังไม่ได้บันทึก) ใช้กับตัวอย่าง PDF ในหน้า Settings"""
    header = load_header(db)
    for field in FIELDS:
        if field in values:
            header[field] = clean_value(field, values[field]) or DEFAULTS[field]
    return header


def save_header(db: Session, values: dict, updated_by: str) -> dict[str, str]:
    for field in FIELDS:
        if field not in values:
            continue

        value = clean_value(field, values[field])

        key = KEY_PREFIX + field
        row = db.get(AppSetting, key)

        # ว่าง หรือเท่ากับค่าเริ่มต้น = ไม่ต้องเก็บ (กลับไปใช้ค่าเริ่มต้น)
        if not value or value == DEFAULTS[field]:
            if row:
                db.delete(row)
            continue

        if row:
            row.value = value
            row.updated_by = updated_by
        else:
            db.add(AppSetting(key=key, value=value, updated_by=updated_by))

    db.commit()
    return load_header(db)
