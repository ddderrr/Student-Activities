# ค่าตั้งของ Transcript PDF (แก้ที่นี่ที่เดียว)
# ตอนนี้ยังเป็นเดโม: ข้อความในวงเล็บเหลี่ยมคือ placeholder รอข้อมูลจริง

from pathlib import Path

# เดือนเริ่มปีการศึกษา: ดู academic_calendar.py (ใช้ร่วมกับหน้า Student Skills)

UNIVERSITY_NAME = "มหาวิทยาลัยเชียงใหม่"
UNIVERSITY_NAME_EN = "Chiang Mai University"
FACULTY_NAME = "คณะวิทยาศาสตร์"
FACULTY_NAME_EN = "Faculty of Science, Chiang Mai University"
FACULTY_SHORT_NAME_EN = "Faculty of Science"

DOCUMENT_TITLE = "ใบรับรองการเข้าร่วมกิจกรรมนักศึกษา"
DOCUMENT_TITLE_EN = "Student Activity Transcript"

# โลโก้: ใส่ path ไฟล์รูป (PNG/SVG) เช่น Path(__file__).parent / "assets" / "logo.png"
# None = แสดงกล่องข้อความ LOGO_PLACEHOLDER_TEXT แทน
LOGO_PATH: Path | None = None
LOGO_PLACEHOLDER_TEXT = "[โลโก้คณะ]"
LOGO_PLACEHOLDER_TEXT_EN = "[Faculty logo]"

SIGNER_NAME = "[ชื่อ-สกุล ผู้ลงนาม]"
SIGNER_POSITION = "[ตำแหน่ง ผู้ลงนาม]"
SIGNER_NAME_EN = "[Signer name]"
SIGNER_POSITION_EN = "[Signer position]"

# ช่องทางตรวจสอบเอกสาร (ท้ายกระดาษ)
VERIFY_TEXT = "ตรวจสอบความถูกต้องของเอกสารได้ที่ [ช่องทางตรวจสอบเอกสาร]"
VERIFY_TEXT_EN = "Verify this document at [verification channel]"

# เลขที่เอกสาร: {prefix}-{ปีการศึกษา}-{เลขสุ่ม} ตอนนี้ไม่ได้บันทึกลง DB (เดโม)
DOCUMENT_NUMBER_PREFIX = "SCI-TR"

# ลายน้ำ: ยังตรวจสอบเอกสารไม่ได้จริง จึงต้องมีคำว่า "ตัวอย่าง" เสมอจนกว่าจะมีระบบตรวจสอบ
WATERMARK_TEXT = "ตัวอย่าง"
WATERMARK_TEXT_EN = "SAMPLE"

# ฟอนต์ (อยู่ใน backend/fonts ลิขสิทธิ์ SIL OFL)
FONT_DIR = Path(__file__).resolve().parent / "fonts"
