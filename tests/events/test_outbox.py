"""Transactional outbox and relay — TST-DATA-008 · STEP-006.06.

WHAT THESE ARE PROTECTING
    Two failures that a straightforward relay produces by default:

      phantom event   -> the broker heard about something the database rolled back
      mass dead-letter-> a twenty-minute broker outage empties the whole backlog
                         into a queue a human must replay by hand, having lost
                         ordering, while nothing was ever actually broken
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from dbcheck import DSN, requires_db
from outbox import (
    MAX_ATTEMPTS,
    BatchOutcome,
    DeadLetter,
    Envelope,
    OutboxError,
    OutboxRow,
    Publisher,
    Relay,
    Status,
    backoff_for,
    dead_letter_depth,
    oldest_pending_age,
    should_dead_letter,
)

NOW = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
ORG = "cccc0000-0000-0000-0000-00000000000c"


def envelope(event_id: str = "e-1", *, occurred_at: datetime = NOW) -> Envelope:
    return Envelope(
        event_id=event_id,
        event_type="journey.trip.brief_confirmed.v1",
        occurred_at=occurred_at,
        recorded_at=occurred_at,
        tenant_id=ORG,
        correlation_id="corr-1",
        actor="user-1",
        schema_version=1,
        payload_ids={"trip_id": "t-1"},
    )


def row(event_id: str = "e-1", *, attempts: int = 0, occurred_at: datetime = NOW) -> OutboxRow:
    return OutboxRow(
        envelope=envelope(event_id, occurred_at=occurred_at), order_key="t-1", attempts=attempts
    )


class AcceptingPublisher(Publisher):
    def __init__(self) -> None:
        self.sent: list[Envelope] = []

    def publish(self, envelope: Envelope) -> None:
        self.sent.append(envelope)


class RefusingPublisher(Publisher):
    def publish(self, envelope: Envelope) -> None:
        raise ConnectionError("broker unreachable")


class PoisonPublisher(Publisher):
    """Fails one specific message and accepts everything else."""

    def __init__(self, poison_id: str) -> None:
        self.poison_id = poison_id
        self.sent: list[Envelope] = []

    def publish(self, envelope: Envelope) -> None:
        if envelope.event_id == self.poison_id:
            raise ValueError("unserialisable payload")
        self.sent.append(envelope)


# --- the distinction the module exists for -------------------------------------------


class TestAnOutageIsNotAPoisonMessage:
    def test_a_total_outage_dead_letters_nothing(self) -> None:
        """The failure the obvious relay produces: a twenty-minute broker outage
        burns every message's attempts and empties the backlog into a queue a human
        must replay by hand, ordering lost, while nothing was ever broken."""
        relay = Relay(publisher=RefusingPublisher())
        exhausted = [row(f"e-{i}", attempts=MAX_ATTEMPTS) for i in range(3)]
        outcome, updated = relay.run(exhausted, now=NOW)

        assert outcome.looks_like_an_outage is True
        assert relay.dead_letters() == ()
        assert all(r.status is Status.PENDING for r in updated)

    def test_one_failing_message_among_successes_is_dead_lettered(self) -> None:
        """A message only becomes poison once it can be seen failing on its own."""
        relay = Relay(publisher=PoisonPublisher("e-2"))
        rows = [row("e-1"), row("e-2", attempts=MAX_ATTEMPTS), row("e-3")]
        outcome, updated = relay.run(rows, now=NOW)

        assert outcome.looks_like_an_outage is False
        assert len(relay.dead_letters()) == 1
        assert relay.dead_letters()[0].envelope.event_id == "e-2"
        assert dead_letter_depth(updated) == 1

    def test_a_message_below_the_cap_is_retried_even_among_successes(self) -> None:
        relay = Relay(publisher=PoisonPublisher("e-2"))
        _, updated = relay.run([row("e-1"), row("e-2", attempts=1)], now=NOW)
        poisoned = next(r for r in updated if r.envelope.event_id == "e-2")
        assert poisoned.status is Status.PENDING
        assert poisoned.attempts == 2

    def test_eligibility_alone_does_not_condemn(self) -> None:
        """The two conditions, stated separately so the second is not lost."""
        exhausted = row(attempts=MAX_ATTEMPTS)
        assert exhausted.eligible_for_dead_letter is True
        assert should_dead_letter(exhausted, BatchOutcome(published=0, failed=3)) is False
        assert should_dead_letter(exhausted, BatchOutcome(published=2, failed=1)) is True

    def test_an_empty_batch_is_not_an_outage(self) -> None:
        """Nothing published because nothing was queued. A relay with no work must
        not read as a broker failure."""
        assert BatchOutcome(published=0, failed=0).looks_like_an_outage is False


# --- delivery semantics --------------------------------------------------------------


class TestAtLeastOnce:
    def test_a_row_is_marked_published_only_after_the_broker_accepts(self) -> None:
        publisher = AcceptingPublisher()
        _, updated = Relay(publisher=publisher).run([row()], now=NOW)
        assert len(publisher.sent) == 1
        assert updated[0].status is Status.PUBLISHED

    def test_a_failed_publish_leaves_the_row_pending_for_retry(self) -> None:
        _, updated = Relay(publisher=RefusingPublisher()).run([row()], now=NOW)
        assert updated[0].status is Status.PENDING
        assert updated[0].attempts == 1
        assert "ConnectionError" in (updated[0].last_error or "")

    def test_republishing_a_delivered_row_is_refused(self) -> None:
        """A duplicate the transport caused is expected; a duplicate the relay chose
        is a bug, and `.07` should not have to absorb both."""
        delivered = OutboxRow(envelope=envelope(), order_key="t-1", status=Status.PUBLISHED)
        with pytest.raises(OutboxError, match="not pending"):
            Relay(publisher=AcceptingPublisher()).run([delivered], now=NOW)

    @pytest.mark.parametrize(("attempt", "expected"), [(1, 1), (2, 2), (3, 4), (4, 8), (20, 300)])
    def test_backoff_grows_and_is_capped(self, attempt: int, expected: int) -> None:
        """Capped so a long outage does not push the next attempt past the point
        anyone is still watching."""
        assert backoff_for(attempt) == timedelta(seconds=expected)

    def test_attempts_are_counted_from_one(self) -> None:
        with pytest.raises(OutboxError, match="counted from 1"):
            backoff_for(0)


# --- the dead letter itself -------------------------------------------------------------


class TestADeadLetterIsAMessageNotARecordOfFailure:
    def test_the_full_envelope_is_preserved(self) -> None:
        """You dead-letter precisely so it can be sent again once the cause is
        fixed. An error and a message id is a record that something failed."""
        relay = Relay(publisher=PoisonPublisher("e-2"))
        relay.run([row("e-1"), row("e-2", attempts=MAX_ATTEMPTS)], now=NOW)
        letter = relay.dead_letters()[0]
        assert letter.envelope.payload_ids == {"trip_id": "t-1"}
        assert letter.envelope.correlation_id == "corr-1"
        assert letter.order_key == "t-1"

    def test_a_dead_letter_without_a_reason_is_refused(self) -> None:
        with pytest.raises(OutboxError, match="records why"):
            DeadLetter(envelope=envelope(), order_key="t-1", attempts=5, reason=" ", at=NOW)


# --- the metric ---------------------------------------------------------------------------


class TestLagIsMeasuredFromWhenTheFactHappened:
    def test_a_stalled_relay_shows_growing_lag(self) -> None:
        """A relay that died an hour ago has zero time since its last attempt — the
        metric it would naturally publish reads healthiest exactly when it is most
        wrong. Measured from `occurred_at`, the lag grows on its own."""
        stalled = [row("e-1", occurred_at=NOW - timedelta(hours=1))]
        assert oldest_pending_age(stalled, now=NOW) == timedelta(hours=1)

    def test_an_empty_queue_has_no_lag(self) -> None:
        assert oldest_pending_age([], now=NOW) == timedelta(0)

    def test_published_rows_do_not_count_toward_lag(self) -> None:
        published = OutboxRow(
            envelope=envelope(occurred_at=NOW - timedelta(days=2)),
            order_key="t-1",
            status=Status.PUBLISHED,
        )
        assert oldest_pending_age([published], now=NOW) == timedelta(0)


# --- the envelope -------------------------------------------------------------------------------


class TestEnvelopeInvariants:
    def test_an_event_without_a_tenant_is_refused(self) -> None:
        """`REQ-SEC-001`. A consumer cannot scope an untenanted event, so it either
        drops it or leaks it."""
        with pytest.raises(OutboxError, match="carries a tenant"):
            Envelope(
                event_id="e",
                event_type="journey.trip.brief_confirmed.v1",
                occurred_at=NOW,
                recorded_at=NOW,
                tenant_id="  ",
                correlation_id="c",
                actor=None,
                schema_version=1,
                payload_ids={},
            )

    def test_naive_timestamps_are_refused(self) -> None:
        with pytest.raises(OutboxError, match="timezone-aware"):
            Envelope(
                event_id="e",
                event_type="journey.trip.brief_confirmed.v1",
                occurred_at=datetime(2026, 8, 26, 12, 0),  # noqa: DTZ001
                recorded_at=NOW,
                tenant_id=ORG,
                correlation_id="c",
                actor=None,
                schema_version=1,
                payload_ids={},
            )


# --- against the database ---------------------------------------------------------------------------


@pytest.mark.security
@requires_db
class TestTheOutboxCommitsWithItsTransaction:
    def test_a_rolled_back_transaction_leaves_no_event(self) -> None:
        """**No phantom events.** The whole reason the table exists rather than a
        direct publish: the broker cannot join a database transaction, so either the
        event goes out and the state rolls back, or the state commits and the
        publish fails."""
        org = uuid.UUID(ORG)
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'outbox','O') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO outbox (organization_id, event_type, order_key, "
                    "correlation_id, payload_ids) VALUES (%s, %s, 't-1', 'c-1', '{}')",
                    (org, "journey.trip.brief_confirmed.v1"),
                )
            conn.rollback()
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM outbox WHERE organization_id = %s", (org,))
            found = cur.fetchone()
            assert found is not None and found[0] == 0
            cur.execute("DELETE FROM organizations WHERE id = %s", (org,))

    def test_a_malformed_event_type_cannot_reach_the_stream(self) -> None:
        """Checked at the table so a producer's typo fails here, where the producer
        is still in the room, rather than at schema validation on the far end."""
        org = uuid.UUID(ORG)
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'outbox2','O') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            with pytest.raises(psycopg.errors.CheckViolation, match="event_type_shape"):
                cur.execute(
                    "INSERT INTO outbox (organization_id, event_type, order_key, "
                    "correlation_id, payload_ids) VALUES (%s, 'TripConfirmed', 't-1', 'c', '{}')",
                    (org,),
                )
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM organizations WHERE id = %s", (org,))

    def test_the_application_cannot_mark_its_own_event_delivered(self) -> None:
        """A producer that can set `status` can mark an event published without
        sending it, and the relay would never look at it again."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("SELECT has_table_privilege('journeylab_app', 'outbox', 'UPDATE')")
            found = cur.fetchone()
            assert found is not None and found[0] is False

    def test_a_dead_lettered_row_must_carry_its_reason(self) -> None:
        org = uuid.UUID(ORG)
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'outbox3','O') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            with pytest.raises(psycopg.errors.CheckViolation, match="dead_letter_has_a_reason"):
                cur.execute(
                    "INSERT INTO outbox (organization_id, event_type, order_key, "
                    "correlation_id, payload_ids, status) "
                    "VALUES (%s, 'journey.trip.brief_confirmed.v1', 't', 'c', '{}', 'dead_letter')",
                    (org,),
                )
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM organizations WHERE id = %s", (org,))
