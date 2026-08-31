-- JourneyLab — 013 consumer idempotency
-- STEP-006.07 · REQ-DATA-009 · BR-056
--
-- THE ROW AND THE EFFECT COMMIT TOGETHER, OR NEITHER DOES
--   Two orderings are available and both are wrong on their own:
--     effect, then record  -> a crash in between replays the effect. Duplicated.
--     record, then effect  -> a crash in between means the effect never happens
--                             and never will, because the record says it did.
--   The second is worse: a duplicate is visible, a silent omission is not. So the
--   consumer writes this row inside the same transaction as its effect, and the
--   ordering within that transaction stops mattering.
--
-- PRUNING REOPENS THE WINDOW THIS TABLE EXISTS TO CLOSE
--   The table grows without bound, so it must be pruned. But an event older than
--   the prune horizon has no record, and replaying it applies the effect again —
--   which means the horizon must exceed the longest replay anyone may perform.
--   That is a constraint BETWEEN two policies, and nothing enforces it unless it
--   is written down. `pruned_before` records the horizon so a replay can refuse to
--   cross it rather than silently double-applying.
--
-- Expand phase: additive. Safe to revert.

BEGIN;

CREATE TABLE IF NOT EXISTS processed_events (
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  -- The envelope's event_id. `EVENT_CONTRACTS` §3: "Idempotent by event_id."
  event_id         uuid NOT NULL,
  -- Which consumer processed it. The same event is legitimately processed by
  -- several consumers, and keying by event alone would let the first one to
  -- finish suppress the rest.
  consumer         text NOT NULL,
  order_key        text NOT NULL,
  occurred_at      timestamptz NOT NULL,
  processed_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (consumer, event_id)
);

COMMENT ON TABLE processed_events IS
  'REQ-DATA-009. Written in the same transaction as the effect. Keyed by
   (consumer, event_id) because one event is legitimately processed by several
   consumers.';

-- The replay floor. One row per consumer, holding the point before which
-- processed-event records have been discarded — so a replay reaching further back
-- than this would re-apply effects with nothing left to stop it.
CREATE TABLE IF NOT EXISTS consumer_prune_horizon (
  consumer       text PRIMARY KEY,
  pruned_before  timestamptz NOT NULL,
  updated_at     timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE consumer_prune_horizon IS
  'STEP-006.07. The oldest event a replay may safely reach. Beyond it the
   idempotency records are gone and a replay would double-apply.';

CREATE INDEX IF NOT EXISTS processed_events_org_key_idx
  ON processed_events (organization_id, order_key, occurred_at);
CREATE INDEX IF NOT EXISTS processed_events_occurred_idx
  ON processed_events (occurred_at);

ALTER TABLE processed_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_events FORCE  ROW LEVEL SECURITY;
DROP POLICY IF EXISTS processed_events_tenant_isolation ON processed_events;
CREATE POLICY processed_events_tenant_isolation ON processed_events
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

GRANT SELECT, INSERT, DELETE ON processed_events TO journeylab_app;
GRANT SELECT, INSERT, UPDATE ON consumer_prune_horizon TO journeylab_app;

COMMIT;
