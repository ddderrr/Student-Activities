"""บัญชี mock สำหรับหน้า /login (POST /api/auth/login) ใช้ตอนพัฒนาเท่านั้น

นักศึกษายังไม่มีรหัสผ่านของตัวเอง: login ด้วยรหัสร่วมค่าเดียว เฉพาะตอนเปิด
ADMIN_BYPASS_ENABLED ระหว่างที่ยังไม่มี CMU IT Account SSO นักศึกษาทุกคนในตาราง
students (รวมที่ import จากหน้า Settings) login ด้วยอีเมลของตัวเองได้ ถอดออกเมื่อทำ
CMU OAuth นักศึกษาจำลองแต่ละสาขาใช้อีเมลเดียวกัน (ดู
migration_mock_student_login_emails.sql)

อีเมลหนึ่งมีนักศึกษาหลายคน จึงระบุไว้ที่นี่ว่า login แล้วจะได้นักศึกษาคนไหน
(คนที่มีข้อมูลทดสอบ: กิจกรรม, external activity, notification) ข้อมูลจริง
(ชื่อ, สาขา, คณะ) อ่านจากตาราง students เสมอ
"""

STUDENT_MOCK_PASSWORD = "1234"

# อีเมล login -> student_id ที่ได้เมื่อเข้าสู่ระบบ
STUDENT_LOGIN_ACCOUNTS = {
    "chem@test.com": "670510001",
    "cs@test.com": "670510002",
    # นักศึกษาเดโม Transcript (seed_transcript_demo_data.sql)
    "demo@test.com": "670510999",
}
