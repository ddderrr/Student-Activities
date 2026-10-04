-- Existing activities retain zero hours until explicitly configured.
ALTER TABLE activities ADD COLUMN IF NOT EXISTS activity_hours NUMERIC(10,2) NOT NULL DEFAULT 0;
ALTER TABLE external_activities ADD COLUMN IF NOT EXISTS activity_hours NUMERIC(10,2) NOT NULL DEFAULT 0;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_activity_hours_nonnegative' AND conrelid='activities'::regclass) THEN
  ALTER TABLE activities ADD CONSTRAINT ck_activity_hours_nonnegative CHECK (activity_hours >= 0);
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_external_hours_nonnegative' AND conrelid='external_activities'::regclass) THEN
  ALTER TABLE external_activities ADD CONSTRAINT ck_external_hours_nonnegative CHECK (activity_hours >= 0);
 END IF;
END $$;
