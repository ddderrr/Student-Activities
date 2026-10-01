import secrets
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import admin_accounts  # noqa: E402
import main as main_module  # noqa: E402
from database import Base, get_db  # noqa: E402


CENTRAL_ADMIN_EMAIL = "central@test.local"
CHEM_ADMIN_EMAIL = "chem@test.local"
CS_ADMIN_EMAIL = "cs@test.local"

TEST_ADMIN_ACCOUNTS = [
    {"email": CENTRAL_ADMIN_EMAIL, "name": "Central Admin", "major": None},
    {"email": CHEM_ADMIN_EMAIL, "name": "Chemistry Admin", "major": "เคมี"},
    {"email": CS_ADMIN_EMAIL, "name": "CS Admin", "major": "วิทยาการคอมพิวเตอร์"},
]


@asynccontextmanager
async def _noop_lifespan(app):
    # ข้าม lifespan จริง (ที่เชื่อมต่อ Postgres dev) ระหว่างเทส
    yield


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    # ทุกเทสต์เขียนไฟล์หลักฐานลง tmp แทน backend/uploads จริง
    directory = tmp_path / "uploads"
    directory.mkdir()
    monkeypatch.setattr(main_module, "EXTERNAL_ACTIVITY_UPLOAD_DIR", directory)
    return directory


@pytest.fixture(autouse=True)
def auth_secret(monkeypatch):
    # ทุกเทสต์ใช้ AUTH_SECRET สุ่มของตัวเอง ไม่พึ่งค่าตายตัวในโค้ดหรือ .env
    monkeypatch.setenv("AUTH_SECRET", secrets.token_urlsafe(48))


@pytest.fixture(autouse=True)
def admin_bypass(monkeypatch):
    # เทสต์ใช้บัญชีแอดมินชุดคงที่ ไม่ผูกกับรายชื่อจริงใน admin_accounts.py
    monkeypatch.setenv("ADMIN_BYPASS_ENABLED", "true")
    monkeypatch.setattr(admin_accounts, "ADMIN_ACCOUNTS", TEST_ADMIN_ACCOUNTS)


@pytest.fixture()
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[get_db] = override_get_db
    main_module.app.router.lifespan_context = _noop_lifespan

    # เทสต์เดิมเรียก endpoint ฝั่ง admin ได้เหมือนเดิมในฐานะแอดมินกลาง
    with TestClient(
        main_module.app,
        headers={"X-Admin-Email": CENTRAL_ADMIN_EMAIL},
    ) as test_client:
        yield test_client

    main_module.app.dependency_overrides.clear()


@pytest.fixture()
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = TestingSessionLocal()

    yield session

    session.close()
