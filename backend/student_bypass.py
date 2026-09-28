"""รายชื่ออีเมลนักศึกษาทดสอบสำหรับโหมด bypass (เลือกได้ที่หน้า /student/login)

ต่างจาก admin_accounts.py ตรงที่ข้อมูลจริง (ชื่อ, สาขา, คณะ) ไม่ได้เก็บซ้ำที่นี่
แต่อ่านจากตาราง students เสมอ (นักศึกษามีตารางอยู่แล้ว ไม่เหมือนแอดมิน) -- ไฟล์นี้
เก็บแค่อีเมลที่อนุญาตให้เลือกจากหน้า login

เพิ่ม mock student ใหม่ = เพิ่มแถวใน students (ดู migration_seed_mock_students.sql)
แล้วเพิ่มอีเมลที่นี่
"""

STUDENT_BYPASS_EMAILS = [
    "chem_student@test.local",
    "cs_student@test.local",
]
