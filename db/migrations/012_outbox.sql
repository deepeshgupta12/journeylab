-- JourneyLab — 012 transactional outbox
-- STEP-006.06 · REQ-DATA-008, REQ-NFR-005 · BR-055
--
-- WHY A TABLE AND NOT A DIRECT PUBLISH
--   Publishing inside the transaction cannot work: the broker has no way to join
--   a database transaction, so either the event goes out and the transaction rolls
--   back (a phantom event describing something that never happened) or the
--   transaction commits and the publish fails (a lost event). The outbox makes the
--   event part of the same commit, and moves the only remaining failure — the
--   relay — to a place where retrying is safe.
--
-- THE ROW IS MARKED, NEVER DELETED, WHEN PUBLISHED
--   Until it is acknowledged this row is the ONLY place the event exists. A relay
--   that deletes on publish has no way to answer "did this actually go out" after
--   a crash between the send and the delete, and no way to replay. Archival is a
--   later, separate decision with the row still present to archive.
--
-- ORDERING IS PER AGGREGATE AND NOWHERE ELSE
--   `EVENT_CONTRACTS` §3: "Never infer ordering across aggregates. Only per-trip
--   order is guaranteed." The index leads with the order key so a relay can read
--   one aggregate's events in sequence; there is deliberately no global sequence
--   column, because a column that looks like a total order will be used as one.
--
-- Expand phase: additive. Safe to revert.

BEGIN;

CREATE TABLE IF NOT EXISTS outbox (
  -- The envelope's `event_id`, and the idempotency key every consumer uses.
  -- Generated here rather than by the relay: the identity of an event is decided
  -- when the fact happens, not when it is transmitted, and a relay-assigned id
  -- would change on retry.
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  event_type       text NOT NULL,
  -- `journey.<aggregate>.<past-tense-fact>.v<major>`, checked here so a malformed
  -- type cannot reach the stream and fail schema validation at the far end, where
  -- the producer is no longer in the room.
  CONSTRAINT outbox_event_type_shape CHECK (event_type ~ '^journey\.[a-z_]+\.[a-z_]+\.v[0-9]+$'),
  -- What the event is about. Used as the ordering key; never assumed to order
  -- anything outside its own aggregate.
  order_key        text NOT NULL,
  correlation_id   text NOT NULL,
  actor_id         text,
  schema_version   integer NOT NULL DEFAULT 1,
  -- IDs and classifications only. `EVENT_CONTRACTS` §2: never trip content,
  -- evidence prose, personal data or precise location — which is what keeps
  -- deletion tractable, because an event stream full of content is a store that
  -- REQ-PRIV-006 would have to traverse and cannot.
  payload_ids      jsonb NOT NULL,
  occurred_at      timestamptz NOT NULL DEFAULT now(),
  recorded_at      timestamptz NOT NULL DEFAULT now(),

  -- Lifecycle, per STEP-006 §10.
  status           text NOT NULL DEFAULT 'pending',
  attempts         integer NOT NULL DEFAULT 0,
  last_attempt_at  timestamptz,
  last_error       text,
  published_at     timestamptz,
  acknowledged_at  timestamptz,

  CONSTRAINT outbox_status_known
    CHECK (status IN ('pending','published','acknowledged','dead_letter')),
  CONSTRAINT outbox_attempts_non_negative CHECK (attempts >= 0),
  -- A published row records when. Without this, "published" is a word rather than
  -- a fact, and lag cannot be computed for the rows that matter most.
  CONSTRAINT outbox_published_has_a_time
    CHECK ((status IN ('published','acknowledged')) = (published_at IS NOT NULL)),
  -- A dead-lettered row must say why. A dead letter with no reason is a message
  -- nobody can triage, which is the same as a message nobody kept.
  CONSTRAINT outbox_dead_letter_has_a_reason
    CHECK (status <> 'dead_letter' OR last_error IS NOT NULL)
);

COMMENT ON TABLE outbox IS
  'DATA-008 delivery. Written in the aggregate transaction (REQ-DATA-008); marked,
   never deleted, on publish. Payload carries IDs only — content in the stream is a
   store REQ-PRIV-006 deletion would have to traverse.';

-- Relay scan: the pending queue, oldest first, ordered within an aggregate.
CREATE INDEX IF NOT EXISTS outbox_pending_idx
  ON outbox (organization_id, order_key, occurred_at)
  WHERE status = 'pending';

-- Lag and DLQ depth for ALRT-QUEUE-001.
CREATE INDEX IF NOT EXISTS outbox_status_idx ON outbox (status, occurred_at);

ALTER TABLE outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox FORCE  ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outbox_tenant_isolation ON outbox;
CREATE POLICY outbox_tenant_isolation ON outbox
  USING (organization_id = app_current_org())
  WITH CHECK (organization_id = app_current_org());

-- The application writes events; it does not get to mark them published or
-- dead-lettered. That is the relay's job, and a producer that can set `status`
-- can mark its own event delivered without sending it.
GRANT SELECT, INSERT ON outbox TO journeylab_app;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'journeylab_relay') THEN
    CREATE ROLE journeylab_relay NOLOGIN NOBYPASSRLS;
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO journeylab_relay;
GRANT SELECT, UPDATE ON outbox TO journeylab_relay;
GRANT EXECUTE ON FUNCTION app_current_org() TO journeylab_relay;
-- The relay reads and marks the outbox and reaches nothing else. It is the one
-- component that runs without a user, so its blast radius is worth restricting.
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM journeylab_relay;
GRANT SELECT, UPDATE ON outbox TO journeylab_relay;

COMMIT;
