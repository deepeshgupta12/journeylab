-- STEP-002.07 — Audit event emission and runtime flag primitives
-- REQ-SEC-007 (immutable, separate, redacted audit) · REQ-PLAT-012 (flags without redeploy)
--
-- APPEND-ONLY IS ENFORCED BY THE DATABASE, NOT BY CONVENTION
--   The sub-step asks that "no update or delete path exists in code". Code can be
--   changed; a privilege cannot be talked around. `journeylab_app` is granted
--   INSERT and SELECT on audit_events and nothing else, so an UPDATE or DELETE
--   fails at the database even if someone writes one — including in a migration
--   run as that role, and including an ORM doing it implicitly.
--
--   The table owner can still modify rows. That is unavoidable in PostgreSQL and
--   is why the application never connects as the owner (STEP-002.01).
--
-- Idempotent: safe to re-run.

BEGIN;

CREATE TABLE IF NOT EXISTS audit_events (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid,                                  -- NULL for pre-tenant events (user provisioning)
  actor_id        uuid,                                  -- NULL for system-initiated events
  action          text        NOT NULL,
  subject         text        NOT NULL,                  -- what was acted upon
  outcome         text        NOT NULL,
  correlation_id  text,
  payload         jsonb       NOT NULL DEFAULT '{}'::jsonb,
  occurred_at     timestamptz NOT NULL,                  -- when it happened (supplied by the emitter)
  recorded_at     timestamptz NOT NULL DEFAULT now(),    -- when we durably stored it
  CONSTRAINT audit_events_action_shape  CHECK (action ~ '^[a-z_]+\.[a-z_]+$'),
  CONSTRAINT audit_events_outcome_known CHECK (outcome IN ('allowed', 'denied', 'error')),
  -- occurred_at must be timezone-aware and not absurdly future-dated. A clock-skewed
  -- emitter writing year 3000 would sort above every real event forever.
  CONSTRAINT audit_events_occurred_sane CHECK (occurred_at < now() + interval '1 day')
);

COMMENT ON TABLE audit_events IS
  'Append-only security and business audit trail (REQ-SEC-007). Separate from application logs. '
  'journeylab_app holds INSERT and SELECT only — UPDATE and DELETE are refused by the database.';

CREATE INDEX IF NOT EXISTS audit_events_org_time_idx   ON audit_events (organization_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS audit_events_action_idx     ON audit_events (action, occurred_at DESC);
CREATE INDEX IF NOT EXISTS audit_events_actor_idx      ON audit_events (actor_id, occurred_at DESC);

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE  ROW LEVEL SECURITY;

-- Tenant-scoped reads. Rows with a NULL organization_id are pre-tenant events
-- (a user provisioned before belonging to any organization) and are visible to no
-- tenant — deliberately, since they belong to none.
DROP POLICY IF EXISTS audit_events_tenant_isolation ON audit_events;
CREATE POLICY audit_events_tenant_isolation ON audit_events
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id IS NULL OR organization_id = app_current_org());

-- --- feature flags ----------------------------------------------------------
--
-- Scope: NULL organization_id is the global default; a row with an organization_id
-- overrides it for that tenant. Evaluation prefers the tenant row.

-- NOTE: `PRIMARY KEY (key, organization_id)` cannot express this, because primary
-- key columns are implicitly NOT NULL — so the NULL-means-global row could never
-- be inserted. A surrogate key plus two PARTIAL unique indexes gives the intended
-- shape and correct uniqueness on both sides.
CREATE TABLE IF NOT EXISTS feature_flags (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  key             text        NOT NULL,
  organization_id uuid,                                  -- NULL = global default
  value           jsonb       NOT NULL,
  updated_at      timestamptz NOT NULL DEFAULT now(),
  updated_by      uuid
);

COMMENT ON TABLE feature_flags IS
  'Runtime flags (REQ-PLAT-012). A MISSING row is not an error: evaluation falls back to the '
  'caller-declared conservative value, so an empty table means every feature is off.';

-- Exactly one global row per key, and one override per (key, tenant). Without the
-- partial indexes, duplicates would make evaluation non-deterministic.
CREATE UNIQUE INDEX IF NOT EXISTS feature_flags_global_key_idx
  ON feature_flags (key) WHERE organization_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS feature_flags_tenant_key_idx
  ON feature_flags (key, organization_id) WHERE organization_id IS NOT NULL;

ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags FORCE  ROW LEVEL SECURITY;

-- A tenant may read its own overrides and the global defaults; it may write neither.
-- Flag changes are an administrative act (STEP-021), not something a request performs.
DROP POLICY IF EXISTS feature_flags_read ON feature_flags;
CREATE POLICY feature_flags_read ON feature_flags
  FOR SELECT
  USING (organization_id IS NULL OR organization_id = app_current_org());

-- --- privileges: this is where append-only actually lives -------------------

GRANT SELECT, INSERT ON audit_events  TO journeylab_app;
REVOKE UPDATE, DELETE ON audit_events FROM journeylab_app;

GRANT SELECT           ON feature_flags  TO journeylab_app;
REVOKE INSERT, UPDATE, DELETE ON feature_flags FROM journeylab_app;

COMMIT;
