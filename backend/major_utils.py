"""normalize ชื่อสาขา (major) ให้เหมือนกันทั้งระบบ"""


def normalize_major(value: str | None) -> str | None:
    """ตัดช่องว่างหน้า-หลัง ค่าว่าง = ไม่มีสาขา (None)"""
    return (value or "").strip() or None
