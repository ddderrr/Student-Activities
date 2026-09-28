"""ปฏิทินการศึกษา: ใช้ร่วมกันทั้งระบบ (Transcript PDF, หน้า Student Skills, seed_demo_data)

แก้เดือนเริ่มปีการศึกษาที่นี่ที่เดียว
"""

from datetime import date, datetime

# ปีการศึกษาเริ่มเดือนไหน (1-12) เช่น 7 = 1 ก.ค. ถึง 30 มิ.ย. ปีถัดไป
# หมายเหตุ: หน้า Student Skills แบ่งภาคเรียนตามปฏิทิน (ม.ค.-มิ.ย. / ก.ค.-ธ.ค.)
# ถ้าเปลี่ยนเป็นเดือนอื่น ภาคเรียนจะนับเป็นปีการศึกษาที่ครอบเดือนส่วนใหญ่
ACADEMIC_YEAR_START_MONTH = 7


def academic_year_of(value: date | datetime) -> int:
    """ปีการศึกษา (พ.ศ.) ของวันที่"""
    day = value.date() if isinstance(value, datetime) else value
    buddhist_year = day.year + 543

    if day.month >= ACADEMIC_YEAR_START_MONTH:
        return buddhist_year

    return buddhist_year - 1
