-- JourneyLab — 001 identity and tenancy
-- STEP-002.01 · REQ-SEC-001, REQ-SEC-002 · BR-008 (HIGH risk)
--
-- THE CONVENTION EVERY LATER MIGRATION INHERITS:
--   1. Every tenant-scoped table carries a non-null organization_id.
--   2. ENABLE *and* FORCE row level security. Without FORCE, the table owner
--      silently bypasses every policy — the most common way RLS is believed
--      present but absent.
--   3. The application connects as a NON-OWNER role that cannot bypass RLS.
--   4. Tenant context is set per transaction with SET LOCAL, never per
--      connection — a pooler reusing a connection would otherwise leak context
--      between tenants.
--   5. Indexes lead with organization_id.
--
-- Expand phase: additive only. Safe to revert.

BEGIN;

-- ── Extensions this migration depends on ──────────────────────────────────────
-- Declared here rather than relying on local init SQL: a migration must be
-- self-contained so it applies identically to a managed production database that
-- never runs infra/local/postgres/init/.
CREATE EXTENSION IF NOT EXISTS citext;      -- case-insensitive email
CREATE EXTENSION IF NOT EXISTS pgcrypto;    -- gen_random_uuid() on older servers

-- ── Tenant context ────────────────────────────────────────────────────────────
-- Read by every RLS policy. SET LOCAL scopes it to the transaction, so a pooled
-- connection cannot carry one tenant's context into another's transaction.
CREATE OR REPLACE FUNCTION app_current_org() RETURNS uuid
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_org', true), '')::uuid
$$;

COMMENT ON FUNCTION app_current_org() IS
  'Current tenant for RLS. NULL when unset, which denies all access by design (REQ-SEC-001).';

-- ── Core tables ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS organizations (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug          text NOT NULL UNIQUE,
  display_name  text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE organizations IS 'DATA-001. Tenant boundary. Not itself tenant-scoped.';

CREATE TABLE IF NOT EXISTS users (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  -- Subject from the identity provider. DEC-004 is still open, so this is a
  -- provider-neutral opaque string rather than a vendor-specific column.
  idp_subject   text UNIQUE,
  email         citext UNIQUE,
  locale        text NOT NULL DEFAULT 'en',
  time_zone     text NOT NULL DEFAULT 'UTC',
  is_guest      boolean NOT NULL DEFAULT false,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  -- REQ-PRIV-001: a guest plans without an account, so both identifiers may be
  -- null. A non-guest must be identifiable.
  CONSTRAINT users_identifiable_unless_guest
    CHECK (is_guest OR idp_subject IS NOT NULL OR email IS NOT NULL)
);
COMMENT ON TABLE users IS
  'DATA-002. No inferred sensitive traits (REQ-PRIV-003) — accessibility, age and
   mobility live in TravelerProfile and are set only by explicit declaration.';

CREATE TABLE IF NOT EXISTS roles (
  key          text PRIMARY KEY,
  description  text NOT NULL
);
COMMENT ON TABLE roles IS 'Role keys from AUTHORIZATION_MATRIX §2. Reference data, not tenant-scoped.';

INSERT INTO roles (key, description) VALUES
  ('guest',            'Unauthenticated session with a claimed trip'),
  ('trip_owner',       'Trip creator; sole authority over canonical selection'),
  ('trip_editor',      'Invited collaborator with edit scope'),
  ('trip_viewer',      'Invited collaborator, read and comment'),
  ('advisor',          'Organization member with delegated, audited client access'),
  ('curator',          'Internal: destination facts only, no traveler PII'),
  ('ops_admin',        'Internal: providers, flags, incidents; no raw PII by default'),
  ('privacy_operator', 'Internal: executes data-subject requests, audited'),
  ('service',          'Workload identity with narrow capability')
ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS memberships (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_key         text NOT NULL REFERENCES roles(key),
  created_at       timestamptz NOT NULL DEFAULT now(),
  expires_at       timestamptz,
  revoked_at       timestamptz,
  UNIQUE (organization_id, user_id, role_key)
);
COMMENT ON TABLE memberships IS
  'Tenant-scoped. expires_at/revoked_at support REQ-TRIP-006 expiring, revocable access.';

CREATE TABLE IF NOT EXISTS service_identities (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name             text NOT NULL,
  -- REQ-SEC-003: workload identity only. There is deliberately NO column for a
  -- static secret — a credential that cannot be stored cannot be leaked.
  workload_subject text NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  revoked_at       timestamptz,
  UNIQUE (organization_id, name)
);
COMMENT ON TABLE service_identities IS
  'REQ-SEC-003. No static-key column exists by design.';

-- ── Indexes (organization_id leads) ───────────────────────────────────────────
CREATE INDEX IF NOT EXISTS memberships_org_user_idx        ON memberships (organization_id, user_id);
CREATE INDEX IF NOT EXISTS memberships_org_role_idx        ON memberships (organization_id, role_key);
CREATE INDEX IF NOT EXISTS service_identities_org_idx      ON service_identities (organization_id);

-- ── Row-level security ────────────────────────────────────────────────────────
ALTER TABLE memberships         ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships         FORCE  ROW LEVEL SECURITY;
ALTER TABLE service_identities  ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_identities  FORCE  ROW LEVEL SECURITY;
ALTER TABLE organizations       ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations       FORCE  ROW LEVEL SECURITY;

-- Deny-by-default: app_current_org() returns NULL when unset, so every
-- comparison is NULL and no row qualifies. Missing context denies access.
DROP POLICY IF EXISTS memberships_tenant_isolation ON memberships;
CREATE POLICY memberships_tenant_isolation ON memberships
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

DROP POLICY IF EXISTS service_identities_tenant_isolation ON service_identities;
CREATE POLICY service_identities_tenant_isolation ON service_identities
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

DROP POLICY IF EXISTS organizations_self_isolation ON organizations;
CREATE POLICY organizations_self_isolation ON organizations
  USING (id = app_current_org())
  WITH CHECK (id = app_current_org());

-- ── Application role ──────────────────────────────────────────────────────────
-- Non-owner, and explicitly NOBYPASSRLS. The migration owner keeps DDL rights;
-- the application never connects as the owner.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'journeylab_app') THEN
    CREATE ROLE journeylab_app NOLOGIN NOBYPASSRLS;
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO journeylab_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON organizations, users, memberships, service_identities TO journeylab_app;
GRANT SELECT ON roles TO journeylab_app;
GRANT EXECUTE ON FUNCTION app_current_org() TO journeylab_app;

COMMIT;
