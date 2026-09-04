-- JourneyLab — 016 coverage is platform data, not tenant data
-- STEP-007.01 · REQ-EVID-006, REQ-TRIP-002 · BUG-028
--
-- THE DEFECT THIS CORRECTS
--   STEP-006.09 built `coverage_read_model` tenant-scoped, with `organization_id`
--   NOT NULL and FORCE ROW LEVEL SECURITY. The operation that exists to serve it —
--   `getCoverage`, `API-017` — is declared `security: []`: **public and
--   unauthenticated**, because a traveller must be able to learn whether their
--   destination is supported before creating an account.
--
--   A public request has no tenant to bind, so `app_current_org()` is NULL, so
--   every RLS comparison is NULL, so no row qualifies. Reproduced before writing
--   this migration: one row present, zero rows visible.
--
--   The failure mode is what makes it worth a migration rather than a workaround.
--   The endpoint does not error. It returns an empty region list — **"we support
--   nowhere"** — which is a well-formed, plausible, completely wrong answer about
--   coverage, served to the person deciding whether to sign up.
--
-- WHY GLOBAL IS THE CORRECT MODEL AND NOT JUST THE CONVENIENT ONE
--   Whether Bern is supported is a property of our providers, not of who is asking.
--   Two tenants do not have different coverage. This is the same reasoning that
--   kept `places` and `place_provider_ids` out of tenant scope in `BR-046` §7:
--   reference data scoped per tenant fragments the thing it describes.
--
--   The contract settles it independently. An unauthenticated operation cannot
--   return tenant-scoped data, because there is no tenant — so either the data is
--   global or the endpoint is wrong, and the endpoint is the product requirement.
--
-- THIS IS A CONTRACT-PHASE MIGRATION, AND THAT IS STATED RATHER THAN SMUGGLED
--   STEP-006 §24: contract-phase migrations do not revert cleanly and run only
--   after the rollout window closes with no reader remaining. Both conditions hold
--   here and are checked rather than assumed: these tables were created three days
--   ago, nothing outside the test suite reads them, and no deployment exists. The
--   expand/contract ceremony would be theatre over an empty table — but the phase
--   is named, because the next one will not be empty.

BEGIN;

-- ── coverage_read_model: platform reference data ─────────────────────────────
DROP POLICY IF EXISTS coverage_read_model_tenant_isolation ON coverage_read_model;
ALTER TABLE coverage_read_model NO FORCE ROW LEVEL SECURITY;
ALTER TABLE coverage_read_model DISABLE ROW LEVEL SECURITY;

-- Rebuilding the primary key first: region_id alone identifies a region now, and
-- it must, or two rows could describe the same place.
ALTER TABLE coverage_read_model DROP CONSTRAINT IF EXISTS coverage_read_model_pkey;
DELETE FROM coverage_read_model a USING coverage_read_model b
  WHERE a.ctid < b.ctid AND a.region_id = b.region_id;
ALTER TABLE coverage_read_model DROP COLUMN IF EXISTS organization_id;
ALTER TABLE coverage_read_model ADD PRIMARY KEY (region_id);

DROP INDEX IF EXISTS coverage_read_model_org_idx;
CREATE INDEX IF NOT EXISTS coverage_read_model_accepting_idx
  ON coverage_read_model (accepting_trips);

COMMENT ON TABLE coverage_read_model IS
  'REQ-EVID-006 / REQ-TRIP-002. **Platform data, deliberately not tenant-scoped**
   (BUG-028): API-017 is public and unauthenticated, so a tenant-scoped row is a
   row the endpoint can never read. No provider column — the public view names no
   supplier, and a column here would be the place it leaks.';

-- ── projection_position: a global projection has a global position ───────────
-- A tenant-scoped projection, when one exists, gets its own position table. One
-- table serving both scopes is how an isolation boundary stops being legible —
-- and the RLS policy for the tenant case cannot express "or this row is global",
-- because NULL never satisfies it.
DROP POLICY IF EXISTS projection_position_tenant_isolation ON projection_position;
ALTER TABLE projection_position NO FORCE ROW LEVEL SECURITY;
ALTER TABLE projection_position DISABLE ROW LEVEL SECURITY;

ALTER TABLE projection_position DROP CONSTRAINT IF EXISTS projection_position_pkey;
DELETE FROM projection_position a USING projection_position b
  WHERE a.ctid < b.ctid AND a.projection = b.projection;
ALTER TABLE projection_position DROP COLUMN IF EXISTS organization_id;
ALTER TABLE projection_position ADD PRIMARY KEY (projection);

COMMENT ON TABLE projection_position IS
  'REQ-DATA-010. Watermark for **global** projections. A tenant-scoped projection
   gets its own position table rather than a nullable tenant column, because NULL
   never satisfies an RLS policy and a half-scoped table is worse than two.';

COMMIT;
