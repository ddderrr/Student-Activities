"""normalize ชื่อคณะ (students.faculty) ให้เหมือนกันทั้งระบบ"""

DEFAULT_FACULTY = "Faculty of Science"

# ชื่อคณะวิทยาศาสตร์ที่เจอในไฟล์ import (เทียบแบบไม่สนตัวพิมพ์เล็กใหญ่)
_SCIENCE_FACULTY_NAMES = {"คณะวิทยาศาสตร์", DEFAULT_FACULTY.casefold()}


def normalize_faculty(value: str | None) -> str:
    """ตัดช่องว่างหน้า-หลัง ค่าว่าง / คณะวิทยาศาสตร์ = DEFAULT_FACULTY"""
    faculty = (value or "").strip()
    if not faculty or faculty.casefold() in _SCIENCE_FACULTY_NAMES:
        return DEFAULT_FACULTY
    return faculty
