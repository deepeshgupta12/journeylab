-- JourneyLab — 015 read models and projection position
-- STEP-006.09 · REQ-DATA-010 · BR-058
--
-- A READ MODEL IS DERIVED, AND THE SCHEMA SAYS SO
--   Nothing here is a source of truth. Every row is reconstructible from the event
--   log, which is why a corrupt projection is an inconvenience rather than data
--   loss — and why `rebuilt_at` is on every row: a projection that cannot say when
--   it was last derived cannot be told apart from one that stopped updating.
--
-- POSITION IS PER PROJECTION, NOT GLOBAL
--   Two projections rebuild independently and at different speeds. One shared
--   cursor would make the slower one's progress look like the faster one's.
--
-- Expand phase: additive. Safe to revert — dropping a read model loses nothing that
-- the log cannot produce again, which is the whole property being claimed.

BEGIN;

CREATE TABLE IF NOT EXISTS projection_position (
  projection      text NOT NULL,
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  -- The last event this projection has folded in. Ordering is per key, so this is
  -- a watermark rather than a sequence number — see STEP-006.07 on why timestamps
  -- are not a total order.
  last_event_id   uuid,
  last_occurred_at timestamptz,
  -- Distinguishes "caught up" from "never ran". A projection at position NULL and
  -- a projection with no events are the same row otherwise, and only one of them
  -- is a problem.
  rebuilt_at      timestamptz,
  updated_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (projection, organization_id)
);

COMMENT ON TABLE projection_position IS
  'REQ-DATA-010. Per-projection watermark. Two projections rebuild at different
   speeds, so a shared cursor would misreport both.';

-- The first projection. `PublicCoverage` in STEP-005.10 is the shape it serves, and
-- it carries no provider identity for the same reason that type does not.
CREATE TABLE IF NOT EXISTS coverage_read_model (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  region_id       text NOT NULL,
  freshness       text NOT NULL,
  accepting_trips boolean NOT NULL,
  limitations     jsonb NOT NULL DEFAULT '[]'::jsonb,
  rebuilt_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, region_id),
  CONSTRAINT coverage_freshness_known CHECK (freshness IN ('current','degraded','stale'))
);

COMMENT ON TABLE coverage_read_model IS
  'REQ-EVID-006 / REQ-TRIP-002. Derived from EVT-008. **No provider column** — the
   public view names no supplier, and a column here would be the place that leaks.';

CREATE INDEX IF NOT EXISTS coverage_read_model_org_idx
  ON coverage_read_model (organization_id, accepting_trips);

ALTER TABLE projection_position   ENABLE ROW LEVEL SECURITY;
ALTER TABLE projection_position   FORCE  ROW LEVEL SECURITY;
ALTER TABLE coverage_read_model   ENABLE ROW LEVEL SECURITY;
ALTER TABLE coverage_read_model   FORCE  ROW LEVEL SECURITY;

DROP POLICY IF EXISTS projection_position_tenant_isolation ON projection_position;
CREATE POLICY projection_position_tenant_isolation ON projection_position
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

DROP POLICY IF EXISTS coverage_read_model_tenant_isolation ON coverage_read_model;
CREATE POLICY coverage_read_model_tenant_isolation ON coverage_read_model
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

GRANT SELECT, INSERT, UPDATE, DELETE ON projection_position TO journeylab_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON coverage_read_model TO journeylab_app;

COMMIT;
