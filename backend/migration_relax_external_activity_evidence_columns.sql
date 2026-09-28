-- Run this ONCE on the existing PostgreSQL database (safe to re-run).
--
-- external_activities.evidence_filename / evidence_original_name /
-- evidence_content_type / evidence_size are legacy single-file columns from
-- before multi-evidence-file support was added (see external_activity_evidence
-- table). models.py already marks all 4 as nullable=True, but create_all()
-- never alters columns on a table that already exists, so this DB was still
-- enforcing the old NOT NULL constraint -- any new submission (which only
-- writes rows to external_activity_evidence, not these 4 columns) failed
-- with a NotNullViolation.

ALTER TABLE external_activities ALTER COLUMN evidence_filename DROP NOT NULL;
ALTER TABLE external_activities ALTER COLUMN evidence_original_name DROP NOT NULL;
ALTER TABLE external_activities ALTER COLUMN evidence_content_type DROP NOT NULL;
ALTER TABLE external_activities ALTER COLUMN evidence_size DROP NOT NULL;
