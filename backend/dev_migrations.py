"""Apply the existing, non-destructive schema upgrades for local development."""
from pathlib import Path


def apply_development_migrations(engine):
    if engine.dialect.name != "postgresql":
        return

    directory = Path(__file__).resolve().parent
    with engine.begin() as connection:
        # Serialize concurrent dev startups. Each script is safe to run again.
        connection.exec_driver_sql("SELECT pg_advisory_xact_lock(730194)")
        for filename in (
            "migration_add_activity_major.sql",
            "migration_add_activity_hours.sql",
            "migration_add_activity_status.sql",
            "migration_add_reject_reason.sql",
            "migration_relax_external_activity_evidence_columns.sql",
        ):
            connection.exec_driver_sql((directory / filename).read_text(encoding="utf-8"))
