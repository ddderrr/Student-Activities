import sys
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as main_module  # noqa: E402
from database import Base, get_db  # noqa: E402


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

    with TestClient(main_module.app) as test_client:
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
