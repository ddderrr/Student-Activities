# รายชื่อแอดมินทดสอบสำหรับโหมด bypass (ADMIN_BYPASS_ENABLED=true) ใช้ตอนพัฒนาเท่านั้น
# แก้รายชื่อที่นี่ที่เดียว หน้า login ฝั่ง admin ดึงรายชื่อจาก backend
#
# major: ต้องสะกดตรงกับ students.major ทุกตัวอักษร
#        None = แอดมินกลางของคณะ เห็นทุกสาขา รวมนักศึกษาที่ไม่มีสาขา

ADMIN_ACCOUNTS = [
    {
        "email": "central@test.local",
        "name": "แอดมินกลาง คณะวิทยาศาสตร์",
        "major": None,
    },
    {
        "email": "chem@test.local",
        "name": "แอดมินสาขาเคมี",
        "major": "เคมี",
    },
    {
        "email": "cs@test.local",
        "name": "แอดมินสาขาวิทยาการคอมพิวเตอร์",
        "major": "วิทยาการคอมพิวเตอร์",
    },
]
