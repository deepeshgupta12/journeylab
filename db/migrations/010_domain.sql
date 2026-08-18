-- JourneyLab — 010 canonical domain model
-- STEP-006.01 · REQ-DATA-007, REQ-SEC-001 · BR-050 (HIGH risk, low reversibility)
--
-- INHERITS EVERY CONVENTION FROM 001, WHICH IS NOT RESTATED HERE:
--   organization_id non-null · ENABLE *and* FORCE RLS · non-owner app role ·
--   SET LOCAL tenant context · indexes leading with organization_id.
--
-- THREE THINGS THIS MIGRATION DOES THAT A SCHEMA USUALLY DOES NOT:
--
--   1. IMMUTABILITY IS ENFORCED, NOT DOCUMENTED. TripBrief, EvidencePack and
--      ScenarioVersion reject UPDATE at the database. REQ-CONS-006 makes a run
--      reproducible from its inputs; if an input can be edited after the fact,
--      "reproducible" means "reproduces whatever it says now", which is not a
--      property anybody can rely on. A comment saying "do not update" is not a
--      constraint.
--
--   2. IMMUTABLE IS NOT UNDELETABLE. DELETE stays permitted on all three.
--      REQ-PRIV-006 requires deletion to traverse every store, and a table that
--      cannot be deleted from would make the right to erasure unimplementable —
--      a privacy defect created by a reproducibility control. Only UPDATE is
--      blocked, and the distinction is the point.
--
--   3. BOOKING REFERENCES LIVE IN THEIR OWN SCHEMA WITH THEIR OWN ROLE.
--      Segregation by grant rather than by convention: `journeylab_app` — the
--      role every planning query runs as — is never granted USAGE on the
--      `booking` schema, so a planning-side SQL injection reaches nothing there.
--      There is also no column for a payment credential, which is the same
--      construction as the affiliate attribution record in STEP-005.06: the
--      field a leak would need does not exist to be filled in.
--
-- WHAT IS DELIBERATELY NOT MODELLED YET
--   Columns whose shape belongs to a later step are absent rather than guessed:
--   the itinerary DAG (STEP-011), ranking features (STEP-012), repair options
--   (STEP-017). Each is a jsonb payload column with a NOT NULL schema_version
--   beside it, so the owning step adds structure by expand migration without
--   this one having invented its design.
--
-- Expand phase: additive only. Safe to revert — no existing table is altered.

BEGIN;

-- ── Shared helpers ────────────────────────────────────────────────────────────

-- Blocks UPDATE on append-only tables. A trigger rather than only a revoked
-- grant, because the grant binds `journeylab_app` and the migration owner would
-- still be able to edit history; reproducibility has to hold against both.
CREATE OR REPLACE FUNCTION app_forbid_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION
    '% is append-only: UPDATE is refused (REQ-CONS-006). Supersede the row with a '
    'new version instead. DELETE remains permitted so REQ-PRIV-006 erasure stays '
    'possible.', TG_TABLE_NAME
    USING ERRCODE = 'restrict_violation';
END $$;

COMMENT ON FUNCTION app_forbid_update() IS
  'STEP-006.01. Immutability for reproducibility, without blocking erasure.';

-- ── DATA-003 TravelerProfile ──────────────────────────────────────────────────
-- Versioned: one row per change, never edited in place, so a scenario generated
-- last week can still name the preferences it was generated from.
CREATE TABLE IF NOT EXISTS traveler_profiles (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  version          integer NOT NULL,
  -- REQ-PRIV-003: DECLARED ONLY. Every entry needs a source and a consent
  -- reference, so an inferred trait has nowhere to be written without lying
  -- about where it came from.
  accessibility    jsonb NOT NULL DEFAULT '[]'::jsonb,
  preferences      jsonb NOT NULL DEFAULT '{}'::jsonb,
  declared_by      text NOT NULL,
  consent_id       uuid,
  schema_version   integer NOT NULL DEFAULT 1,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, user_id, version),
  CONSTRAINT traveler_profiles_declared_only
    CHECK (declared_by IN ('traveler', 'advisor_on_behalf'))
);
COMMENT ON TABLE traveler_profiles IS
  'DATA-003. Sensitive. REQ-PRIV-003 — declaration only; there is no inference path.';

-- ── DATA-004 Trip ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trips (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  owner_user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title            text NOT NULL,
  status           text NOT NULL DEFAULT 'draft',
  starts_on        date,
  ends_on          date,
  time_zone        text NOT NULL,
  -- Set when a scenario is selected. Nullable because most of a trip's life is
  -- spent before that point.
  canonical_scenario_id uuid,
  -- NULL means undecided, NOT unlimited — the same distinction LicenceRecord
  -- draws for cache duration. Retention defaults need the privacy owner
  -- (STEP-006 §27) and inventing one here would be a policy nobody approved.
  retention_days   integer,
  version          integer NOT NULL DEFAULT 1,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT trips_status_known CHECK (status IN (
    'draft','brief_confirmed','evidence_ready','generating','scenarios_ready',
    'infeasible','failed','selected','activated','replanning','completed','archived')),
  CONSTRAINT trips_dates_ordered CHECK (ends_on IS NULL OR starts_on IS NULL OR ends_on >= starts_on)
);
COMMENT ON TABLE trips IS 'DATA-004. Status values mirror BACKEND_ARCHITECTURE §3.';

-- ── DATA-005 TripBrief — IMMUTABLE ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trip_briefs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  trip_id          uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  version          integer NOT NULL,
  -- FOUR CONSTRAINT CLASSES IN FOUR COLUMNS, never merged into one list.
  -- constraint-class.json: merging hard and soft "produces a solver that quietly
  -- relaxes a wheelchair requirement to save nine minutes"; merging inferred into
  -- either "hides that a machine put words in the traveller's mouth".
  hard_constraints       jsonb NOT NULL DEFAULT '[]'::jsonb,
  soft_constraints       jsonb NOT NULL DEFAULT '[]'::jsonb,
  inferred_constraints   jsonb NOT NULL DEFAULT '[]'::jsonb,
  unresolved_questions   jsonb NOT NULL DEFAULT '[]'::jsonb,
  confirmed_by_user_id   uuid NOT NULL REFERENCES users(id),
  schema_version   integer NOT NULL DEFAULT 1,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, trip_id, version)
);
COMMENT ON TABLE trip_briefs IS
  'DATA-005. Append-only. The four constraint classes stay in four columns.';

-- ── DATA-006 Place, and the provider identifier graph ─────────────────────────
-- Reference data: NOT tenant-scoped. A museum in Bern is the same museum for
-- every tenant, and scoping it per tenant would fragment the canonical graph and
-- multiply every entity-resolution decision (BR-046 §7).
CREATE TABLE IF NOT EXISTS places (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name             text NOT NULL,
  category         text NOT NULL,
  latitude         double precision NOT NULL,
  longitude        double precision NOT NULL,
  time_zone        text NOT NULL,
  schema_version   integer NOT NULL DEFAULT 1,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  -- STEP-005.07: providers emit 0,0 for "unknown". Every unlocated place would
  -- land on the same point and a proximity matcher would merge the lot.
  CONSTRAINT places_not_null_island CHECK (NOT (latitude = 0 AND longitude = 0)),
  CONSTRAINT places_lat_range  CHECK (latitude  BETWEEN -90 AND 90),
  CONSTRAINT places_lon_range  CHECK (longitude BETWEEN -180 AND 180)
);
COMMENT ON TABLE places IS
  'DATA-006. Reference data, deliberately not tenant-scoped — see BR-046 §7.';

CREATE TABLE IF NOT EXISTS place_provider_ids (
  place_id     uuid NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  namespace    text NOT NULL,
  external_id  text NOT NULL,
  -- Whether this namespace denotes at most one venue (STEP-005.07). A `website`
  -- or `address` denotes something coarser and must never carry identity.
  is_identity  boolean NOT NULL,
  recorded_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (namespace, external_id, place_id)
);
COMMENT ON TABLE place_provider_ids IS
  'DATA-006. The provider identifier graph. is_identity records whether the
   namespace may be matched on, so a chain website cannot merge two branches.';

-- ── DATA-007 EvidenceFact — the three time axes ───────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_facts (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  place_id         uuid REFERENCES places(id) ON DELETE SET NULL,
  field_class      text NOT NULL,
  value            jsonb NOT NULL,
  unit             text,
  -- Provenance, matching provenance.json.
  source_id        text NOT NULL,
  licence_id       text NOT NULL,
  confidence       double precision NOT NULL,
  access_label     text NOT NULL,
  -- THE THREE AXES. Named identically to temporal-validity.json so the column and
  -- the contract cannot drift apart under different names.
  observed_at      timestamptz NOT NULL,
  effective_from   timestamptz NOT NULL,
  effective_to     timestamptz,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  schema_version   integer NOT NULL DEFAULT 1,
  CONSTRAINT evidence_facts_confidence_range CHECK (confidence BETWEEN 0 AND 1),
  CONSTRAINT evidence_facts_access_label_known
    CHECK (access_label IN ('public','display_permitted','internal_only')),
  -- effective_to NULL is open-ended, which is NOT expired.
  CONSTRAINT evidence_facts_window_ordered
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
COMMENT ON TABLE evidence_facts IS
  'DATA-007. observed_at / effective_* / recorded_at are three different questions.';

-- ── DATA-008 EvidencePack — IMMUTABLE ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_packs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  trip_id          uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  -- The freeze point. A pack is what a scenario was generated against, so an
  -- edit to it silently rewrites the past of every scenario citing it.
  coverage_report  jsonb NOT NULL,
  fact_count       integer NOT NULL,
  built_at         timestamptz NOT NULL DEFAULT now(),
  schema_version   integer NOT NULL DEFAULT 1,
  CONSTRAINT evidence_packs_fact_count_sane CHECK (fact_count >= 0)
);
COMMENT ON TABLE evidence_packs IS 'DATA-008. Append-only. The reproducibility freeze point.';

CREATE TABLE IF NOT EXISTS evidence_pack_facts (
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  pack_id          uuid NOT NULL REFERENCES evidence_packs(id) ON DELETE CASCADE,
  fact_id          uuid NOT NULL REFERENCES evidence_facts(id) ON DELETE CASCADE,
  PRIMARY KEY (pack_id, fact_id)
);
COMMENT ON TABLE evidence_pack_facts IS 'DATA-008. Pack membership, frozen with the pack.';

-- ── DATA-009 Candidate ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidates (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  trip_id          uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  place_id         uuid REFERENCES places(id) ON DELETE SET NULL,
  -- Ranking features belong to STEP-012 and are not invented here.
  features         jsonb NOT NULL DEFAULT '{}'::jsonb,
  -- REQ-CONS-005: an excluded option carries why. A candidate list that drops
  -- options without reasons cannot produce a minimal conflict set.
  exclusion_reason text,
  schema_version   integer NOT NULL DEFAULT 1,
  recorded_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE candidates IS 'DATA-009. Exclusions keep their reason (REQ-CONS-005).';

-- ── DATA-010 Scenario — lineage is NOT NULL, not convention ───────────────────
CREATE TABLE IF NOT EXISTS scenarios (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  trip_id          uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  -- REQ-CONS-006: reproducible from inputs, config, model versions and seed.
  -- All four are NOT NULL, so an unreproducible scenario cannot be stored — the
  -- requirement is a constraint rather than a habit.
  brief_id         uuid NOT NULL REFERENCES trip_briefs(id),
  pack_id          uuid NOT NULL REFERENCES evidence_packs(id),
  solver_config    jsonb NOT NULL,
  seed             bigint NOT NULL,
  model_versions   jsonb NOT NULL,
  objective        text NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  schema_version   integer NOT NULL DEFAULT 1
);
COMMENT ON TABLE scenarios IS
  'DATA-010. Four lineage columns NOT NULL — REQ-CONS-006 enforced by the schema.';

-- ── DATA-011 ScenarioVersion — IMMUTABLE ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS scenario_versions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  scenario_id      uuid NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
  version          integer NOT NULL,
  -- The itinerary DAG's shape is STEP-011's design. Held as a versioned payload
  -- so that step adds structure by expand migration rather than this one guessing.
  itinerary        jsonb NOT NULL,
  costs            jsonb NOT NULL DEFAULT '{}'::jsonb,
  scores           jsonb NOT NULL DEFAULT '{}'::jsonb,
  change_explanation text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  schema_version   integer NOT NULL DEFAULT 1,
  UNIQUE (organization_id, scenario_id, version)
);
COMMENT ON TABLE scenario_versions IS 'DATA-011. Append-only. One row per edit.';

-- ── DATA-012 ItineraryItem ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS itinerary_items (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  scenario_version_id uuid NOT NULL REFERENCES scenario_versions(id) ON DELETE CASCADE,
  kind             text NOT NULL,
  title            text,
  -- REQ-NFR-012: every itinerary item references a resolved location. Enforced
  -- as a hard block in STEP-006.08 rather than as a NOT NULL here, because a
  -- transit leg legitimately has no single place.
  place_id         uuid REFERENCES places(id) ON DELETE RESTRICT,
  starts_at        timestamptz NOT NULL,
  ends_at          timestamptz NOT NULL,
  time_zone        text NOT NULL,
  cost_amount_minor bigint,
  cost_currency    text,
  -- REQ-CONS-011: an edit touching a protected item is refused until unlocked.
  protected        boolean NOT NULL DEFAULT false,
  completed        boolean NOT NULL DEFAULT false,
  schema_version   integer NOT NULL DEFAULT 1,
  CONSTRAINT itinerary_items_kind_known
    CHECK (kind IN ('activity','transit','rest','booking','buffer')),
  CONSTRAINT itinerary_items_ordered CHECK (ends_at >= starts_at),
  -- Money is integer minor units and a currency, or neither. A bare amount with
  -- no currency is not a price.
  CONSTRAINT itinerary_items_money_complete
    CHECK ((cost_amount_minor IS NULL) = (cost_currency IS NULL)),
  CONSTRAINT itinerary_items_currency_iso
    CHECK (cost_currency IS NULL OR cost_currency ~ '^[A-Z]{3}$')
);
COMMENT ON TABLE itinerary_items IS
  'DATA-012. Money as integer minor units — never floating point.';

-- ── DATA-014 ImpactEvent ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS impact_events (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  trip_id          uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  severity         text NOT NULL,
  confidence       double precision NOT NULL,
  -- Deduplication key, so the same real-world disruption observed twice is one
  -- impact rather than two.
  dedupe_key       text NOT NULL,
  affected_nodes   jsonb NOT NULL DEFAULT '[]'::jsonb,
  observed_at      timestamptz NOT NULL,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  schema_version   integer NOT NULL DEFAULT 1,
  UNIQUE (organization_id, trip_id, dedupe_key),
  CONSTRAINT impact_events_confidence_range CHECK (confidence BETWEEN 0 AND 1),
  CONSTRAINT impact_events_severity_known
    CHECK (severity IN ('info','minor','major','blocking'))
);
COMMENT ON TABLE impact_events IS 'DATA-014. Deduplicated by (tenant, trip, dedupe_key).';

-- ── DATA-015 Feedback ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feedback (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  trip_id          uuid REFERENCES trips(id) ON DELETE CASCADE,
  itinerary_item_id uuid REFERENCES itinerary_items(id) ON DELETE CASCADE,
  submitted_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  label            text NOT NULL,
  comment          text,
  -- Feedback is only usable for the purposes the traveller consented to.
  consent_id       uuid,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  schema_version   integer NOT NULL DEFAULT 1
);
COMMENT ON TABLE feedback IS 'DATA-015. Consent scope travels with the label.';

-- ── DATA-016 ConsentRecord ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS consent_records (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose          text NOT NULL,
  basis            text NOT NULL,
  granted_at       timestamptz NOT NULL,
  -- Withdrawal is recorded, never a deletion of the grant. Erasing the grant
  -- would destroy the evidence that processing was once lawful.
  withdrawn_at     timestamptz,
  schema_version   integer NOT NULL DEFAULT 1,
  CONSTRAINT consent_records_withdrawal_after_grant
    CHECK (withdrawn_at IS NULL OR withdrawn_at >= granted_at)
);
COMMENT ON TABLE consent_records IS
  'DATA-016. Withdrawal is a column, not a delete — the grant is the evidence.';

-- ── DATA-013 BookingReference — SEGREGATED SCHEMA ─────────────────────────────
CREATE SCHEMA IF NOT EXISTS booking;
COMMENT ON SCHEMA booking IS
  'DATA-013. Segregated by grant. journeylab_app is never given USAGE here, so a
   planning-side injection reaches nothing in this schema.';

CREATE TABLE IF NOT EXISTS booking.booking_references (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  trip_id          uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  itinerary_item_id uuid REFERENCES itinerary_items(id) ON DELETE SET NULL,
  partner_id       text NOT NULL,
  -- The partner's own reference. NOT a payment credential, and there is no
  -- column for one: no card number, no PAN, no IBAN, no CVV. STEP-005.06 refuses
  -- payment-shaped fields in the adapter; this is the same rule at rest.
  external_reference text NOT NULL,
  status           text NOT NULL,
  confirmed_at     timestamptz,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  schema_version   integer NOT NULL DEFAULT 1,
  CONSTRAINT booking_references_status_known
    CHECK (status IN ('pending','confirmed','cancelled','failed'))
);
COMMENT ON TABLE booking.booking_references IS
  'DATA-013. No payment-credential column exists by design (REQ-BOOK-002).';

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- Indexes, RLS, immutability and grants
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── Indexes (organization_id leads, per the 001 convention) ───────────────────
CREATE INDEX IF NOT EXISTS traveler_profiles_org_user_idx ON traveler_profiles (organization_id, user_id, version DESC);
CREATE INDEX IF NOT EXISTS trips_org_owner_idx            ON trips (organization_id, owner_user_id);
CREATE INDEX IF NOT EXISTS trips_org_status_idx           ON trips (organization_id, status);
CREATE INDEX IF NOT EXISTS trip_briefs_org_trip_idx       ON trip_briefs (organization_id, trip_id, version DESC);
CREATE INDEX IF NOT EXISTS evidence_facts_org_place_idx   ON evidence_facts (organization_id, place_id);
-- The solver filters on EFFECTIVE time and freshness checks on OBSERVED time.
-- Two indexes because they are two different questions (STEP-006.02).
CREATE INDEX IF NOT EXISTS evidence_facts_org_effective_idx ON evidence_facts (organization_id, effective_from, effective_to);
CREATE INDEX IF NOT EXISTS evidence_facts_org_observed_idx  ON evidence_facts (organization_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS evidence_packs_org_trip_idx     ON evidence_packs (organization_id, trip_id);
CREATE INDEX IF NOT EXISTS evidence_pack_facts_org_idx     ON evidence_pack_facts (organization_id, pack_id);
CREATE INDEX IF NOT EXISTS candidates_org_trip_idx         ON candidates (organization_id, trip_id);
CREATE INDEX IF NOT EXISTS scenarios_org_trip_idx          ON scenarios (organization_id, trip_id);
CREATE INDEX IF NOT EXISTS scenario_versions_org_scen_idx  ON scenario_versions (organization_id, scenario_id, version DESC);
CREATE INDEX IF NOT EXISTS itinerary_items_org_version_idx ON itinerary_items (organization_id, scenario_version_id, starts_at);
CREATE INDEX IF NOT EXISTS impact_events_org_trip_idx      ON impact_events (organization_id, trip_id);
CREATE INDEX IF NOT EXISTS feedback_org_trip_idx           ON feedback (organization_id, trip_id);
CREATE INDEX IF NOT EXISTS consent_records_org_user_idx    ON consent_records (organization_id, user_id, purpose);
CREATE INDEX IF NOT EXISTS booking_refs_org_trip_idx       ON booking.booking_references (organization_id, trip_id);
CREATE INDEX IF NOT EXISTS place_provider_ids_place_idx    ON place_provider_ids (place_id);

-- ── Row-level security on every tenant-scoped table ───────────────────────────
-- `places` and `place_provider_ids` are absent from this list on purpose: they
-- are reference data with no organization_id, and giving them one would fragment
-- the canonical place graph per tenant (BR-046 §7).
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'traveler_profiles','trips','trip_briefs','evidence_facts','evidence_packs',
    'evidence_pack_facts','candidates','scenarios','scenario_versions',
    'itinerary_items','impact_events','feedback','consent_records'
  ] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE  ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', t || '_tenant_isolation', t);
    EXECUTE format(
      'CREATE POLICY %I ON %I USING (organization_id = app_current_org()) '
      'WITH CHECK (organization_id = app_current_org())',
      t || '_tenant_isolation', t);
  END LOOP;
END $$;

ALTER TABLE booking.booking_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking.booking_references FORCE  ROW LEVEL SECURITY;
DROP POLICY IF EXISTS booking_references_tenant_isolation ON booking.booking_references;
CREATE POLICY booking_references_tenant_isolation ON booking.booking_references
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

-- ── Immutability ──────────────────────────────────────────────────────────────
-- Belt and braces, and each half covers what the other cannot: the revoked grant
-- stops the application, the trigger stops everyone including the migration
-- owner. UPDATE only — DELETE stays available so REQ-PRIV-006 erasure works.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['trip_briefs','evidence_packs','scenario_versions'] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', t || '_no_update', t);
    EXECUTE format(
      'CREATE TRIGGER %I BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION app_forbid_update()',
      t || '_no_update', t);
  END LOOP;
END $$;

-- ── Grants ────────────────────────────────────────────────────────────────────
GRANT SELECT, INSERT, UPDATE, DELETE ON
  traveler_profiles, trips, evidence_facts, evidence_pack_facts, candidates,
  scenarios, itinerary_items, impact_events, feedback, consent_records
  TO journeylab_app;

-- Append-only: no UPDATE grant. The trigger is the backstop; this is the fence.
GRANT SELECT, INSERT, DELETE ON trip_briefs, evidence_packs, scenario_versions
  TO journeylab_app;

-- Reference data: readable by the application, written by ingestion.
GRANT SELECT ON places, place_provider_ids TO journeylab_app;

-- ── Booking segregation ───────────────────────────────────────────────────────
-- The planning role is deliberately NOT granted USAGE on this schema. REVOKE is
-- explicit rather than relying on the default, so the intent survives a future
-- `GRANT ... ON ALL SCHEMAS` run by someone in a hurry.
REVOKE ALL ON SCHEMA booking FROM journeylab_app;
REVOKE ALL ON ALL TABLES IN SCHEMA booking FROM journeylab_app;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'journeylab_booking') THEN
    CREATE ROLE journeylab_booking NOLOGIN NOBYPASSRLS;
  END IF;
END $$;

GRANT USAGE ON SCHEMA booking TO journeylab_booking;
GRANT SELECT, INSERT, UPDATE ON booking.booking_references TO journeylab_booking;
GRANT EXECUTE ON FUNCTION app_current_org() TO journeylab_booking;
-- The booking role can reach its own schema and nothing else. Segregation has to
-- cut both ways or it is only a one-directional fence.
REVOKE ALL ON SCHEMA public FROM journeylab_booking;
GRANT USAGE ON SCHEMA public TO journeylab_booking;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM journeylab_booking;

COMMIT;
