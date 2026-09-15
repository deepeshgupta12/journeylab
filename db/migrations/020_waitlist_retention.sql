-- JourneyLab — 020 a waitlist address is not kept forever
-- BUG-036 · DEC-012 · REQ-PRIV-002, REQ-PRIV-006 · BR-065
--
-- THE DEFECT
--   `019` stored an address until its owner withdrew — and for anyone who never
--   withdrew, indefinitely. `STEP-007` §14 says waitlist inquiries "carry a retention
--   period"; `019` had none, because the sub-step it was built from never said so.
--
-- THE RULE (DEC-012, owner decision 2026-09-14)
--   Keep the address until the one message it was given for has been sent, and never
--   longer than 12 calendar months after the grant — whichever comes first. The page
--   promises one message; once it is sent the purpose is exhausted, and a region that
--   never opens must not hold the address for ever by default.
--
-- WHAT THIS MIGRATION CHANGES
--   `notified_at` — set by whatever eventually sends the message. Nothing sends one
--                   yet (email delivery is out of scope), so today only the cap bites.
--   `expired_at`  — set by `expire_waitlist_entries`. A second way for an entry to
--                   end, beside withdrawal.
--
--   `waitlist_active_has_address` is recreated under the SAME NAME with a wider
--   meaning: an entry that has ended — withdrawn OR expired — must hold no address.
--   Same name because the rule is the same rule, now with two ways to end; a new name
--   would leave every reference to the old one describing a constraint that no longer
--   exists.
--
-- WHY THE ROW SURVIVES EXPIRY
--   For the reason it survives withdrawal (`019`): the grant is the evidence that
--   processing was once lawful, and the address is the personal data. Expiry deletes
--   the second and keeps the first.
--
-- SAFE AGAINST EXISTING ROWS
--   Every existing active row has an address and no `expired_at`; every withdrawn row
--   has neither. Both satisfy the widened CHECK, so it is added without a data fix.
--   Checked against the dev database before commit, not assumed.

BEGIN;

ALTER TABLE waitlist_entries ADD COLUMN IF NOT EXISTS notified_at timestamptz;
ALTER TABLE waitlist_entries ADD COLUMN IF NOT EXISTS expired_at  timestamptz;

ALTER TABLE waitlist_entries DROP CONSTRAINT IF EXISTS waitlist_active_has_address;
ALTER TABLE waitlist_entries ADD CONSTRAINT waitlist_active_has_address
  CHECK (
    (withdrawn_at IS NULL AND expired_at IS NULL
       AND email IS NOT NULL AND email_normalized IS NOT NULL)
    OR
    ((withdrawn_at IS NOT NULL OR expired_at IS NOT NULL)
       AND email IS NULL AND email_normalized IS NULL)
  );

ALTER TABLE waitlist_entries DROP CONSTRAINT IF EXISTS waitlist_notified_after_grant;
ALTER TABLE waitlist_entries ADD CONSTRAINT waitlist_notified_after_grant
  CHECK (notified_at IS NULL OR notified_at >= granted_at);

ALTER TABLE waitlist_entries DROP CONSTRAINT IF EXISTS waitlist_expiry_after_grant;
ALTER TABLE waitlist_entries ADD CONSTRAINT waitlist_expiry_after_grant
  CHECK (expired_at IS NULL OR expired_at >= granted_at);

-- The sweep reads only entries still holding an address.
CREATE INDEX IF NOT EXISTS waitlist_retention_due_idx
  ON waitlist_entries (granted_at)
  WHERE withdrawn_at IS NULL AND expired_at IS NULL;

COMMENT ON COLUMN waitlist_entries.notified_at IS
  'When the one promised message was sent. Sending exhausts the purpose, so the next
   retention sweep deletes the address (DEC-012). Nothing sets this yet: email
   delivery does not exist.';

COMMENT ON COLUMN waitlist_entries.expired_at IS
  'When retention ended the entry — notified, or 12 calendar months after the grant
   (DEC-012). The address is deleted; the dated grant survives as evidence, exactly as
   on withdrawal.';

COMMIT;
