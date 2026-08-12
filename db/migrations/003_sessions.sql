-- 003 — Server-side session store and revocation. STEP-002.08.
--
-- WHY THIS MIGRATION EXISTS
--   STEP-002.05 built the session DECISION LOGIC — issue, hash, validate, expire —
--   as pure functions taking a record as a parameter. The record had nowhere to
--   live. Without a store there is no revocation: signing out cleared cookies, and
--   an already-issued token kept working until it expired on its own.
--
-- TWO TABLES, AND THE REASON IS REQ-SEC-001
--   `sessions` is tenant-scoped: organization_id NOT NULL, RLS, the same
--   deny-by-default policy as migration 001.
--
--   `guest_sessions` has NO tenant column, because a guest has no tenant. A guest
--   session precedes authentication.
--
--   The alternative was one table with a nullable organization_id, and it was
--   rejected because the RLS predicate would then have to special-case NULL —
--   which is precisely the shape of a policy that later lets a real row through.
--   A sentinel "no tenant" organization was rejected for a related reason: it
--   would give every guest session the same tenant, so a bug leaking across guest
--   sessions would look like a legitimate same-tenant read.
--
--   Two tables keep both invariants true instead of weakening one to cover both.
--
-- REVOCATION STAMPS, IT DOES NOT DELETE
--   Same rule as memberships in 001. Deleting a session erases the evidence that
--   it existed, which is exactly what an investigation needs after an account
--   compromise: when the session started, when it was ended, and by what.

BEGIN;

-- ── Authenticated sessions (tenant-scoped) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  -- REQ-PRIV-001: the hash, never the token. A leaked table of raw session
  -- tokens would be a leaked set of live sessions.
  --
  -- SHA-256 rather than a slow KDF, deliberately: the token is 256 bits of
  -- CSPRNG output, so there is no dictionary to attack and nothing for a work
  -- factor to buy. The same reasoning as apps/web/src/auth/guest.ts.
  token_hash       text NOT NULL,
  issued_at        timestamptz NOT NULL DEFAULT now(),
  expires_at       timestamptz NOT NULL,
  revoked_at       timestamptz,
  -- Why it ended. An audit trail that records only THAT a session was revoked
  -- cannot distinguish a user signing out from an administrator ending a
  -- compromised session, and those need different responses.
  revoked_reason   text,
  CONSTRAINT sessions_token_hash_unique UNIQUE (token_hash),
  CONSTRAINT sessions_expires_after_issue CHECK (expires_at > issued_at),
  -- A reason without a revocation, or a revocation without a reason, means one of
  -- the two writes was forgotten. Enforced here so neither can be.
  CONSTRAINT sessions_revocation_is_complete
    CHECK ((revoked_at IS NULL) = (revoked_reason IS NULL))
);
COMMENT ON TABLE sessions IS
  'Tenant-scoped authenticated sessions. STEP-002.08. Revocation stamps revoked_at; rows are never deleted.';

-- ── Guest sessions (no tenant, by construction) ───────────────────────────────
CREATE TABLE IF NOT EXISTS guest_sessions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  token_hash       text NOT NULL,
  issued_at        timestamptz NOT NULL DEFAULT now(),
  expires_at       timestamptz NOT NULL,
  revoked_at       timestamptz,
  revoked_reason   text,
  CONSTRAINT guest_sessions_token_hash_unique UNIQUE (token_hash),
  CONSTRAINT guest_sessions_expires_after_issue CHECK (expires_at > issued_at),
  CONSTRAINT guest_sessions_revocation_is_complete
    CHECK ((revoked_at IS NULL) = (revoked_reason IS NULL))
);
COMMENT ON TABLE guest_sessions IS
  'NO organization_id by design: a guest session precedes authentication and has no tenant. STEP-002.08 §6.';

-- ── Indexes ───────────────────────────────────────────────────────────────────
-- organization_id leads, matching 001: every tenant-scoped query filters on it
-- first, so a composite index that does not lead with it is not used.
CREATE INDEX IF NOT EXISTS sessions_org_user_idx ON sessions (organization_id, user_id);
-- Partial: revoke-all and expiry sweeps only ever look at live sessions, and a
-- store that accumulates revoked rows forever would otherwise scan them all.
CREATE INDEX IF NOT EXISTS sessions_live_idx
  ON sessions (organization_id, user_id) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS guest_sessions_live_idx
  ON guest_sessions (expires_at) WHERE revoked_at IS NULL;

-- ── Row-level security ────────────────────────────────────────────────────────
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions FORCE  ROW LEVEL SECURITY;

-- Deny-by-default, identical to 001: app_current_org() returns NULL when unset,
-- every comparison is NULL, no row qualifies. Missing context denies.
DROP POLICY IF EXISTS sessions_tenant_isolation ON sessions;
CREATE POLICY sessions_tenant_isolation ON sessions
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

-- guest_sessions gets NO tenant policy, because it has no tenant to isolate on.
-- That is not an omission, and leaving RLS off entirely would be: it is enabled
-- with a policy that permits the application role and nothing conditional, so the
-- table is reached only through the grants below and a future tenant-scoped query
-- against it fails loudly rather than silently returning another guest's row.
ALTER TABLE guest_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE guest_sessions FORCE  ROW LEVEL SECURITY;
DROP POLICY IF EXISTS guest_sessions_app_access ON guest_sessions;
CREATE POLICY guest_sessions_app_access ON guest_sessions
  USING (true) WITH CHECK (true);
COMMENT ON POLICY guest_sessions_app_access ON guest_sessions IS
  'Unconditional BY DESIGN: a guest session has no tenant. Isolation for guests is the unguessable 256-bit token, not a row predicate.';

-- ── Application role ──────────────────────────────────────────────────────────
-- No DELETE. Revocation stamps a column; the application has no privilege that
-- could remove a session record, so "never deleted" is enforced by the database
-- rather than by remembering to write UPDATE instead of DELETE.
GRANT SELECT, INSERT, UPDATE ON sessions, guest_sessions TO journeylab_app;

COMMIT;
