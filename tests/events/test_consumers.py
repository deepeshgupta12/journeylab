"""Consumer idempotency and replay — TST-DATA-009 · STEP-006.07.

WHAT THESE ARE PROTECTING
    At-least-once delivery makes duplicates certain, so every one of these is a
    normal-operation path rather than an edge case:

      duplicate applied twice  -> a booking confirmed twice, a counter doubled
      record written before
      the effect               -> the effect never happens and never will, because
                                  the record says it did
      replay past the prune
      horizon                  -> effects re-applied with nothing left to stop them,
                                  and the symptom appears long after the replay
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from consumers import (
    ConsumerError,
    IdempotentConsumer,
    ProcessedLog,
    ReplayBeyondHorizonError,
    envelope_from_wire,
    group_by_key,
    in_key_order,
    replay,
)
from outbox import Envelope

NOW = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
ORG = "cccc0000-0000-0000-0000-00000000000c"


def envelope(event_id: str = "e-1", *, at: datetime = NOW, trip: str = "t-1") -> Envelope:
    return Envelope(
        event_id=event_id,
        event_type="journey.trip.brief_confirmed.v1",
        occurred_at=at,
        recorded_at=at,
        tenant_id=ORG,
        correlation_id="corr-1",
        actor="user-1",
        schema_version=1,
        payload_ids={"trip_id": trip},
    )


def counting_consumer(
    *, natural: bool = False, log: ProcessedLog | None = None
) -> tuple[IdempotentConsumer, list[str]]:
    seen: list[str] = []
    consumer = IdempotentConsumer(
        name="coverage",
        handler=lambda e: seen.append(e.event_id),
        log=log or ProcessedLog(),
        naturally_idempotent=natural,
    )
    return consumer, seen


# --- once in effect ------------------------------------------------------------------


class TestDuplicateDeliveryProducesOneEffect:
    def test_the_same_event_twice_runs_the_handler_once(self) -> None:
        """TST-DATA-009. At-least-once makes this the normal path, not an edge."""
        consumer, seen = counting_consumer()
        assert consumer.handle(envelope()) is True
        assert consumer.handle(envelope()) is False
        assert seen == ["e-1"]
        assert (consumer.applied, consumer.skipped) == (1, 1)

    def test_a_failing_handler_leaves_no_record_so_the_retry_still_happens(self) -> None:
        """The ordering that matters. A record written before a failure suppresses
        the retry for ever — the effect never happens, and nothing says so."""
        attempts: list[str] = []

        def flaky(e: Envelope) -> None:
            attempts.append(e.event_id)
            if len(attempts) == 1:
                raise RuntimeError("transient")

        consumer = IdempotentConsumer(name="c", handler=flaky, log=ProcessedLog())
        with pytest.raises(RuntimeError, match="transient"):
            consumer.handle(envelope())
        assert consumer.handle(envelope()) is True
        assert attempts == ["e-1", "e-1"]

    def test_two_consumers_both_process_the_same_event(self) -> None:
        """Keyed by (consumer, event_id). Keying by event alone would let whichever
        consumer finished first suppress every other one."""
        log = ProcessedLog()
        first, first_seen = counting_consumer(log=log)
        second = IdempotentConsumer(name="search", handler=lambda e: None, log=log)
        assert first.handle(envelope()) is True
        assert second.handle(envelope()) is True
        assert first_seen == ["e-1"]

    def test_a_naturally_idempotent_consumer_keeps_no_records(self) -> None:
        """`SET status = 'confirmed'` is safe to repeat, so it costs no unbounded
        table and creates no prune hazard. The handler running twice is correct."""
        consumer, seen = counting_consumer(natural=True)
        consumer.handle(envelope())
        consumer.handle(envelope())
        assert seen == ["e-1", "e-1"]
        assert consumer.log.has_seen("coverage", "e-1") is False


# --- the prune hazard ------------------------------------------------------------------


class TestPruningReopensTheWindowItExistsToClose:
    def test_a_replay_past_the_horizon_is_refused(self) -> None:
        """The whole point. Beyond the horizon the records are gone, so the replay
        would re-apply effects with nothing left to deduplicate them — and the
        symptom shows up downstream long after the replay finished."""
        consumer, _ = counting_consumer()
        consumer.handle(envelope("old", at=NOW - timedelta(days=90)))
        consumer.log.prune_before("coverage", NOW - timedelta(days=30))

        with pytest.raises(ReplayBeyondHorizonError, match="one policy"):
            replay(
                consumer,
                [envelope("old", at=NOW - timedelta(days=90))],
                since=NOW - timedelta(days=60),
            )

    def test_the_refusal_names_both_dates(self) -> None:
        """So the person who chose them can see that they disagree."""
        consumer, _ = counting_consumer()
        consumer.log.prune_before("coverage", NOW - timedelta(days=30))
        with pytest.raises(ReplayBeyondHorizonError) as caught:
            replay(consumer, [], since=NOW - timedelta(days=60))
        message = str(caught.value)
        assert (NOW - timedelta(days=60)).isoformat() in message
        assert (NOW - timedelta(days=30)).isoformat() in message

    def test_a_replay_inside_the_horizon_is_allowed(self) -> None:
        consumer, seen = counting_consumer()
        consumer.log.prune_before("coverage", NOW - timedelta(days=30))
        assert (
            replay(
                consumer,
                [envelope("recent", at=NOW - timedelta(days=1))],
                since=NOW - timedelta(days=7),
            )
            == 1
        )
        assert seen == ["recent"]

    def test_a_replay_processes_only_the_requested_range(self) -> None:
        """An operator asking for "since yesterday" and getting all history back is
        a far larger operation than the one they authorised — a full scan on a
        recorded consumer, and repeated work on a naturally idempotent one.

        The first version of this suite only ever passed events inside the range, so
        a mutant that dropped the filter entirely went unnoticed.
        """
        consumer, seen = counting_consumer(natural=True)
        envelopes = [
            envelope("ancient", at=NOW - timedelta(days=400)),
            envelope("inside", at=NOW - timedelta(days=2)),
        ]
        assert replay(consumer, envelopes, since=NOW - timedelta(days=7)) == 1
        assert seen == ["inside"]

    def test_pruning_moves_the_horizon_in_the_same_call(self) -> None:
        """A prune that does not move the horizon leaves a replay believing it is
        protected by records that no longer exist."""
        log = ProcessedLog()
        log.record("coverage", envelope("old", at=NOW - timedelta(days=90)))
        removed = log.prune_before("coverage", NOW - timedelta(days=30))
        assert removed == 1
        assert log.horizon("coverage") == NOW - timedelta(days=30)

    def test_the_horizon_never_moves_backwards(self) -> None:
        """A later prune with an earlier date would claim protection the records no
        longer provide."""
        log = ProcessedLog()
        log.prune_before("coverage", NOW - timedelta(days=30))
        log.prune_before("coverage", NOW - timedelta(days=90))
        assert log.horizon("coverage") == NOW - timedelta(days=30)

    def test_a_naturally_idempotent_consumer_may_replay_anywhere(self) -> None:
        """It has no records to lose, so the horizon does not constrain it. This is
        the practical argument for preferring naturally idempotent effects."""
        consumer, seen = counting_consumer(natural=True)
        consumer.log.prune_before("coverage", NOW - timedelta(days=30))
        assert (
            replay(
                consumer,
                [envelope("ancient", at=NOW - timedelta(days=900))],
                since=NOW - timedelta(days=1000),
            )
            == 1
        )
        assert seen == ["ancient"]


# --- ordering ---------------------------------------------------------------------------


class TestOrderingIsPerKeyAndNotCausal:
    def test_events_are_grouped_by_key_rather_than_globally_sorted(self) -> None:
        """A consumer handed the whole stream will sort it and believe the result.
        Groups make the guarantee visible in the shape of the data."""
        grouped = group_by_key(
            [envelope("a", trip="t-1"), envelope("b", trip="t-2"), envelope("c", trip="t-1")]
        )
        assert set(grouped) == {"t-1", "t-2"}
        assert [e.event_id for e in grouped["t-1"]] == ["a", "c"]

    def test_a_timestamp_tie_is_broken_deterministically(self) -> None:
        """Clocks have resolution, so two events can share `occurred_at`. Sorting on
        it alone is not deterministic, and two replays would disagree."""
        tied = [envelope("z", at=NOW), envelope("a", at=NOW)]
        assert [e.event_id for e in in_key_order(tied)] == ["a", "z"]
        assert in_key_order(tied) == in_key_order(list(reversed(tied)))

    def test_the_tiebreak_buys_reproducibility_not_causality(self) -> None:
        """Stated as a test because the output looks identical either way, and the
        difference is the thing a reader would otherwise assume away: `event_id`
        order says nothing about which event really happened first.
        """
        earlier_id_later_fact = envelope("a", at=NOW + timedelta(seconds=1))
        later_id_earlier_fact = envelope("z", at=NOW)
        ordered = in_key_order([earlier_id_later_fact, later_id_earlier_fact])
        assert [e.event_id for e in ordered] == ["z", "a"], "the timestamp still leads"


# --- additive tolerance -------------------------------------------------------------------


class TestUnknownFieldsAreIgnored:
    def test_an_extra_field_does_not_break_a_consumer(self) -> None:
        """`EVENT_CONTRACTS` §3. Strict parsing breaks every consumer at once,
        during a deploy whose change log said "additive"."""
        wire = {
            "event_id": "e-1",
            "event_type": "journey.trip.brief_confirmed.v1",
            "occurred_at": NOW,
            "recorded_at": NOW,
            "tenant_id": ORG,
            "correlation_id": "c",
            "schema_version": 2,
            "payload_ids": {"trip_id": "t-1"},
            "a_field_added_next_quarter": {"nested": True},
        }
        parsed = envelope_from_wire(wire)
        assert parsed.event_id == "e-1"
        assert parsed.schema_version == 2

    def test_a_missing_required_field_is_still_an_error(self) -> None:
        """Tolerance is for additions. A missing `tenant_id` is not a new field, it
        is an event nobody can scope."""
        with pytest.raises(ConsumerError, match="missing required field"):
            envelope_from_wire(
                {
                    "event_id": "e-1",
                    "event_type": "journey.trip.brief_confirmed.v1",
                    "occurred_at": NOW,
                    "recorded_at": NOW,
                    "correlation_id": "c",
                    "schema_version": 1,
                }
            )

    def test_an_absent_actor_is_allowed(self) -> None:
        """System-originated events have no user behind them."""
        parsed = envelope_from_wire(
            {
                "event_id": "e-1",
                "event_type": "journey.provider.health_changed.v1",
                "occurred_at": NOW,
                "recorded_at": NOW,
                "tenant_id": ORG,
                "correlation_id": "c",
                "schema_version": 1,
            }
        )
        assert parsed.actor is None


class TestReplayInputsAreRefusedNotGuessed:
    def test_a_naive_replay_start_is_refused(self) -> None:
        consumer, _ = counting_consumer()
        with pytest.raises(ConsumerError, match="timezone-aware"):
            replay(consumer, [], since=datetime(2026, 8, 26, 12, 0))  # noqa: DTZ001

    def test_a_naive_prune_horizon_is_refused(self) -> None:
        with pytest.raises(ConsumerError, match="timezone-aware"):
            ProcessedLog().prune_before("c", datetime(2026, 8, 26, 12, 0))  # noqa: DTZ001
