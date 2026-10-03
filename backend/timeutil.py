"""เวลาของระบบ: ใช้เวลาไทย (Asia/Bangkok, UTC+7) ที่เดียวทั้ง backend

คอลัมน์เวลาส่วนใหญ่เป็น TIMESTAMP ไม่มี timezone จึงเก็บ "เวลานาฬิกาไทย" แบบ naive
ทุกที่ที่สร้างเวลาต้องเรียกจากไฟล์นี้ ไม่ใช่ datetime.now() / date.today() ตรง ๆ
(ซึ่งขึ้นกับ timezone ของเครื่องที่รัน backend และ DB now() ซึ่งขึ้นกับ timezone ของ
session ฐานข้อมูล -- ก่อนหน้านี้สองนาฬิกาไม่ตรงกัน 7 ชั่วโมง ดู B28)
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

BANGKOK = ZoneInfo("Asia/Bangkok")
DB_TIMEZONE = "Asia/Bangkok"


def now_bangkok() -> datetime:
    """เวลาไทยตอนนี้แบบ naive (สำหรับคอลัมน์ TIMESTAMP ไม่มี timezone)"""
    return datetime.now(BANGKOK).replace(tzinfo=None)


def now_bangkok_aware() -> datetime:
    """เวลาไทยตอนนี้แบบมี timezone (สำหรับคอลัมน์ TIMESTAMPTZ)"""
    return datetime.now(BANGKOK)


def today_bangkok() -> date:
    return datetime.now(BANGKOK).date()
