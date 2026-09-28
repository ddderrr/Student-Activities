from datetime import date

import migrate_evidence_files
from models import ExternalActivity, ExternalActivityEvidence, Student

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 8


def create_legacy_request(db_session, upload_dir, stored_name, write_file=True):
    """สภาพหลังรัน SQL migration: มีแถวใน external_activity_evidence แล้ว แต่ไฟล์ยังอยู่ uploads/ ชั้นบน"""
    if not db_session.get(Student, "670510659"):
        db_session.add(
            Student(
                student_id="670510659",
                first_name="Test",
                last_name="Student",
                email="",
                faculty="Faculty of Science",
                major="",
            )
        )
        db_session.commit()

    activity = ExternalActivity(
        student_id="670510659",
        title="Old",
        organization="Org",
        activity_type="Workshop",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 10),
        location="CM",
        role="participant",
        status="pending",
        evidence_filename=stored_name,
        evidence_original_name="old.png",
        evidence_content_type="image/png",
        evidence_size=len(PNG_BYTES),
    )
    db_session.add(activity)
    db_session.commit()

    db_session.add(
        ExternalActivityEvidence(
            external_activity_id=activity.id,
            stored_name=stored_name,
            original_name="old.png",
            content_type="image/png",
            size=len(PNG_BYTES),
        )
    )
    db_session.commit()

    if write_file:
        (upload_dir / stored_name).write_bytes(PNG_BYTES)

    return activity


def test_moves_legacy_files_into_request_folder(db_session, upload_dir):
    first = create_legacy_request(db_session, upload_dir, "aaa.png")
    second = create_legacy_request(db_session, upload_dir, "bbb.png")

    report = migrate_evidence_files.migrate(db_session, upload_dir)

    assert report == {"moved": 2, "already_in_place": 0, "missing": []}
    assert (upload_dir / str(first.id) / "aaa.png").read_bytes() == PNG_BYTES
    assert (upload_dir / str(second.id) / "bbb.png").read_bytes() == PNG_BYTES
    assert not (upload_dir / "aaa.png").exists()
    assert not (upload_dir / "bbb.png").exists()


def test_running_twice_is_safe(db_session, upload_dir):
    activity = create_legacy_request(db_session, upload_dir, "aaa.png")
    migrate_evidence_files.migrate(db_session, upload_dir)

    report = migrate_evidence_files.migrate(db_session, upload_dir)

    assert report == {"moved": 0, "already_in_place": 1, "missing": []}
    assert (upload_dir / str(activity.id) / "aaa.png").exists()


def test_reports_missing_files_without_failing(db_session, upload_dir):
    activity = create_legacy_request(db_session, upload_dir, "gone.png", write_file=False)

    report = migrate_evidence_files.migrate(db_session, upload_dir)

    assert report["moved"] == 0
    assert report["missing"] == [f"{activity.id}/gone.png"]


def test_dry_run_moves_nothing(db_session, upload_dir):
    create_legacy_request(db_session, upload_dir, "aaa.png")

    report = migrate_evidence_files.migrate(db_session, upload_dir, dry_run=True)

    assert report["moved"] == 1
    assert (upload_dir / "aaa.png").exists()
