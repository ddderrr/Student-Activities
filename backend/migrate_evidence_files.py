"""
ย้ายไฟล์หลักฐานของคำขอเก่าจาก uploads/external_activities/<ไฟล์>
ไปไว้ที่ uploads/external_activities/<external_activity_id>/<ไฟล์>

รันหลัง migration_multiple_evidence_files.sql (ต้องมีแถวใน external_activity_evidence แล้ว)
รันซ้ำได้: ไฟล์ที่ย้ายแล้วจะข้าม

    docker compose exec backend python migrate_evidence_files.py --dry-run
    docker compose exec backend python migrate_evidence_files.py
"""

import argparse
import os
from pathlib import Path

from sqlalchemy.orm import Session

from models import ExternalActivityEvidence


def migrate(db: Session, upload_dir: Path, dry_run: bool = False) -> dict:
    report = {"moved": 0, "already_in_place": 0, "missing": []}

    for evidence in db.query(ExternalActivityEvidence).order_by(ExternalActivityEvidence.id):
        name = Path(evidence.stored_name).name
        folder = upload_dir / str(int(evidence.external_activity_id))
        target = folder / name
        legacy = upload_dir / name

        if target.is_file():
            report["already_in_place"] += 1
            continue

        if not legacy.is_file():
            report["missing"].append(f"{evidence.external_activity_id}/{name}")
            continue

        if not dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            os.replace(legacy, target)

        report["moved"] += 1

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="แสดงผลอย่างเดียว ไม่ย้ายไฟล์จริง")
    args = parser.parse_args()

    # import ตอนรันจริง: main ต้องมี DATABASE_URL และกำหนด upload dir ไว้
    from database import SessionLocal
    from main import EXTERNAL_ACTIVITY_UPLOAD_DIR

    with SessionLocal() as db:
        report = migrate(db, EXTERNAL_ACTIVITY_UPLOAD_DIR, dry_run=args.dry_run)

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}moved: {report['moved']}")
    print(f"{prefix}already in place: {report['already_in_place']}")
    print(f"{prefix}missing: {len(report['missing'])}")
    for item in report["missing"]:
        print(f"  - {item}")


if __name__ == "__main__":
    main()
