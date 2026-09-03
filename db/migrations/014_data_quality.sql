-- JourneyLab — 014 data-quality quarantine
-- STEP-006.08 · REQ-DATA-005, REQ-NFR-012 · BR-057
--
-- QUARANTINE IS A PLACE, NOT A LOG LINE
--   §5: "Quarantine visible to curators, not just logged." A failed batch written
--   to a log is a batch nobody can act on: you cannot list it, cannot see how long
--   it has been failing, and cannot release it once the cause is fixed. It is a
--   table for the same reason the review queue in STEP-005.07 is a queue.
--
-- Expand phase: additive. Safe to revert.

BEGIN;

CREATE TABLE IF NOT EXISTS quarantined_batches (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  source_id        text NOT NULL,
  -- Which expectation failed, and on what. A quarantine record that says only
  -- "quality check failed" needs the batch re-run to learn anything, which is the
  -- one thing quarantine exists to avoid.
  expectation      text NOT NULL,
  failure_detail   text NOT NULL,
  record_count     integer NOT NULL,
  -- A hard block cannot be released by a curator; a soft failure can. REQ-NFR-012
  -- makes an unresolved location a block rather than a warning, and the two need
  -- different affordances or the distinction dies in the UI.
  blocking         boolean NOT NULL,
  quarantined_at   timestamptz NOT NULL DEFAULT now(),
  released_at      timestamptz,
  released_by      text,
  CONSTRAINT quarantine_release_is_attributed
    CHECK ((released_at IS NULL) = (released_by IS NULL)),
  -- A blocking failure has no release path. If it could be released, REQ-NFR-012's
  -- "hard block" would be a strongly-worded warning.
  CONSTRAINT quarantine_blocking_is_not_releasable
    CHECK (NOT (blocking AND released_at IS NOT NULL)),
  CONSTRAINT quarantine_detail_present CHECK (length(btrim(failure_detail)) > 0)
);

COMMENT ON TABLE quarantined_batches IS
  'STEP-006.08. Failed batches, listable and releasable by a curator — except
   blocking ones, which by REQ-NFR-012 have no release path.';

CREATE INDEX IF NOT EXISTS quarantine_org_open_idx
  ON quarantined_batches (organization_id, quarantined_at)
  WHERE released_at IS NULL;

ALTER TABLE quarantined_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE quarantined_batches FORCE  ROW LEVEL SECURITY;
DROP POLICY IF EXISTS quarantined_batches_tenant_isolation ON quarantined_batches;
CREATE POLICY quarantined_batches_tenant_isolation ON quarantined_batches
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

GRANT SELECT, INSERT, UPDATE ON quarantined_batches TO journeylab_app;

COMMIT;
