import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from timeutil import DB_TIMEZONE


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "ไม่พบ DATABASE_URL กรุณาสร้าง .env ที่ root ของโปรเจกต์ (หรือ backend/.env) จาก .env.example"
    )


# session ของ PostgreSQL ใช้เวลาไทย: now() / server_default / onupdate ฝั่ง DB
# ตรงกับเวลาจาก timeutil.now_bangkok() (ก่อนหน้านี้ container ฐานข้อมูลเป็น UTC)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=(
        {"options": f"-c timezone={DB_TIMEZONE}"}
        if DATABASE_URL.startswith("postgresql")
        else {}
    ),
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()