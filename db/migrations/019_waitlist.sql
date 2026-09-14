-- JourneyLab — 019 a waitlist entry for somebody who has no account
-- STEP-007.04 · REQ-TRIP-002, REQ-PRIV-002, REQ-PRIV-004, REQ-PRIV-006 · BR-063 §4
--
-- WHY THIS IS NOT A ROW IN `consent_records`
--   `010_domain.sql` created `consent_records` (DATA-016) with `organization_id`
--   NOT NULL, `user_id` NOT NULL, FORCE ROW LEVEL SECURITY, and a tenant-isolation
--   policy. Every one of those is correct for a person who has an account.
--
--   A waitlist subject has no account. They arrived at a public page, learned their
--   destination is not supported, and asked to be told when it is. There is no
--   organization to name and no user to reference, so the row simply cannot be
--   written — and the only ways to make it fit are to invent an organization or to
--   make the isolation columns nullable. The first fabricates a fact; the second
--   weakens the constraint that `R7` exists to protect, on the one table holding
--   consent, so that an unauthenticated endpoint can write to it.
--
--   This is the same shape as `BUG-028`, one layer down. There, a public read met a
--   tenant-scoped read model and returned "we support nowhere". Here a public write
--   meets a tenant-scoped consent table. `016` settled the principle: an
--   unauthenticated operation cannot touch tenant-scoped data, so either the data is
--   platform-level or the endpoint is wrong — and the endpoint is the requirement.
--
--   `STEP-008.04` owns `consent_records` and the account-holder consent model. It
--   inherits the job of reconciling a waitlist grant with a user's consent when the
--   same person later signs up. That is named here rather than discovered there.
--
-- WITHDRAWAL KEEPS THE GRANT AND DESTROYS THE ADDRESS
--   Two rules that sound contradictory, and are not:
--
--     STEP-008.04  "Withdrawal is a column, not a delete — erasing the grant
--                   destroys the evidence that processing was lawful."
--     STEP-007.04  "Email stored against the consent record, deletable on
--                   withdrawal (REQ-PRIV-006)."
--
--   They reconcile exactly: the GRANT is evidence and survives; the ADDRESS is
--   personal data and does not. A withdrawn row records that a lawful grant existed
--   and when it was withdrawn, while holding nothing that identifies anybody. The
--   CHECK constraint below makes that structural rather than a convention — a
--   withdrawn row that still carried an address would fail to persist.
--
-- THE TOKEN IS THE CAPABILITY, AND ONLY ITS HASH IS STORED
--   Withdrawal must work for somebody with no account and no session, and email
--   delivery is out of scope for this sub-step — so there is nothing to send a link
--   through. A high-entropy token is minted at capture and returned once.
--
--   Only its SHA-256 is stored. A database reader can verify a presented token and
--   cannot mint one, which is the same reason a password is not stored either. The
--   hash is not personal data and is retained after withdrawal so a replayed token
--   is recognised rather than mistaken for an unknown one.
--
-- NO ROW LEVEL SECURITY, DECLARED RATHER THAN OMITTED
--   RLS on this table would be inert: `app_current_org()` is NULL on every request
--   that reaches it, so a policy comparing against it would match nothing and the
--   feature would silently never work — `BUG-028` again. The table holds no
--   tenant-scoped data by construction. It is stated here so that a later reader
--   finds a decision instead of an oversight.

BEGIN;

CREATE TABLE IF NOT EXISTS waitlist_entries (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- NULL after withdrawal. `email_normalized` is the lowercased, trimmed form used
  -- for uniqueness; `email` preserves what the person actually typed, because the
  -- local part of an address is case-sensitive by RFC 5321 even though no operator
  -- treats it that way.
  email                  text,
  email_normalized       text,

  -- What they were looking for when they were turned away. Optional, bounded, and
  -- NOT a foreign key: the whole point is that this region is not in coverage.
  region_query           text,

  -- One purpose, enforced by the schema. REQ-PRIV-002 requires purpose-specific
  -- consent, and a `purpose` column that accepts any string is a column that will
  -- eventually hold 'marketing' because somebody passed it.
  purpose                text NOT NULL
                           CHECK (purpose = 'waitlist_notification'),
  basis                  text NOT NULL
                           CHECK (basis = 'consent'),

  granted_at             timestamptz NOT NULL,
  withdrawn_at           timestamptz,

  withdrawal_token_hash  text NOT NULL,
  schema_version         integer NOT NULL DEFAULT 1,

  CONSTRAINT waitlist_withdrawal_after_grant
    CHECK (withdrawn_at IS NULL OR withdrawn_at >= granted_at),

  -- The reconciliation above, made structural. An active row HAS an address; a
  -- withdrawn row has none. Neither state can be written incorrectly, and a future
  -- withdrawal path that forgot to clear the address would fail loudly here rather
  -- than leave personal data behind a withdrawn consent.
  CONSTRAINT waitlist_active_has_address
    CHECK (
      (withdrawn_at IS NULL     AND email IS NOT NULL AND email_normalized IS NOT NULL)
      OR
      (withdrawn_at IS NOT NULL AND email IS NULL     AND email_normalized IS NULL)
    ),

  CONSTRAINT waitlist_email_present
    CHECK (email_normalized IS NULL OR length(btrim(email_normalized)) > 0),
  CONSTRAINT waitlist_region_query_bounded
    CHECK (region_query IS NULL OR length(region_query) <= 64)
);

-- One ACTIVE entry per address, and no constraint at all on withdrawn ones.
--
-- A plain UNIQUE would make withdrawal permanent: having withdrawn, the person
-- could never rejoin, because the tombstone row would still own their address. It
-- would also be unenforceable after withdrawal, since the address is gone by then.
CREATE UNIQUE INDEX IF NOT EXISTS waitlist_active_email_idx
  ON waitlist_entries (email_normalized)
  WHERE withdrawn_at IS NULL;

-- Withdrawal looks a row up by token hash and nothing else.
CREATE UNIQUE INDEX IF NOT EXISTS waitlist_token_idx
  ON waitlist_entries (withdrawal_token_hash);

COMMENT ON TABLE waitlist_entries IS
  'STEP-007.04. Pre-signup consent: no organization_id and no user_id, because the
   subject has neither. Not a substitute for consent_records (DATA-016), which
   STEP-008.04 owns for account holders. Withdrawal keeps the grant as evidence that
   processing was lawful and destroys the address, enforced by
   waitlist_active_has_address rather than by convention.';

COMMENT ON COLUMN waitlist_entries.withdrawal_token_hash IS
  'SHA-256 of a token returned exactly once at capture. Only the hash is stored, so
   a database reader can verify a token and cannot mint one. Retained after
   withdrawal so a replayed token is recognised, not treated as unknown.';

GRANT SELECT, INSERT, UPDATE ON waitlist_entries TO journeylab_app;

COMMIT;
