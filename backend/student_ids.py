"""รูปแบบรหัสนักศึกษาคณะวิทยาศาสตร์ มช.

รหัส 9 หลัก: 2 หลักแรก = ปีที่เข้า (พ.ศ.) หลักที่ 3-5 = รหัสคณะ (051 = คณะวิทยาศาสตร์)
เช่น 670510001 ระบบรับเฉพาะนักศึกษาคณะวิทยาศาสตร์ ทุกจุดที่เพิ่มนักศึกษาเข้าระบบต้องตรวจด้วยฟังก์ชันนี้
"""

import re

SCIENCE_FACULTY_CODE = "051"
# [0-9] ไม่ใช่ \d: \d ของ Python รับเลขไทยและเลขเต็มความกว้างด้วย
SCIENCE_STUDENT_ID_PATTERN = re.compile(rf"^[0-9]{{2}}{SCIENCE_FACULTY_CODE}[0-9]{{4}}$")
INVALID_STUDENT_ID_MESSAGE = "รหัสนักศึกษาต้องเป็นของคณะวิทยาศาสตร์"


def is_science_student_id(value: str | None) -> bool:
    return bool(SCIENCE_STUDENT_ID_PATTERN.fullmatch((value or "").strip()))
