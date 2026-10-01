"""สร้างบัญชีแอดมินเริ่มต้นสำหรับหน้า /login (รันซ้ำได้ ข้ามบัญชีที่มีอยู่แล้ว)

    cd backend && .venv/bin/python seed_admins.py

ใช้ตอนพัฒนา/ทดสอบเท่านั้น: รหัสผ่านทุกบัญชีคือ 1234 เปลี่ยนก่อนใช้งานจริง
"""

from auth_tokens import hash_password
from database import Base, SessionLocal, engine
from models import Admin

DEFAULT_ADMINS = [
    {"email": "central@gmail.com", "first_name": "แอดมินกลาง", "last_name": "คณะวิทยาศาสตร์", "major": None},
    {"email": "chem@gmail.com", "first_name": "แอดมินสาขา", "last_name": "เคมี", "major": "เคมี"},
    {"email": "cs@gmail.com", "first_name": "แอดมินสาขา", "last_name": "วิทยาการคอมพิวเตอร์", "major": "วิทยาการคอมพิวเตอร์"},
]
DEFAULT_PASSWORD = "1234"


def seed_admins(db) -> list[str]:
    created = []

    for account in DEFAULT_ADMINS:
        if db.query(Admin).filter(Admin.email == account["email"]).first():
            continue

        db.add(Admin(**account, password_hash=hash_password(DEFAULT_PASSWORD)))
        created.append(account["email"])

    db.commit()
    return created


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine, tables=[Admin.__table__])

    with SessionLocal() as session:
        created = seed_admins(session)

    print("created:", ", ".join(created) if created else "(none, all exist)")
