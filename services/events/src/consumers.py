"""Consumer idempotency and replay — STEP-006.07 (REQ-DATA-009).

EXACTLY ONCE IN EFFECT, NOT EXACTLY ONCE IN DELIVERY

    The relay is at-least-once and no amount of care makes it otherwise, so
    duplicates are certain rather than possible. What can be made exact is the
    *effect*: process the same event twice and the world ends up in the same place.

    Two ways to get there, and the cheaper one is better:

      naturally idempotent  -> `SET status = 'confirmed'` is safe to repeat. No
                               record needed, no table to grow, nothing to prune.
      recorded              -> everything else. Costs a row per event per consumer,
                               forever, until pruned — and pruning is where the
                               interesting problem is.

    `IdempotentConsumer` prefers the first and falls back to the second, because a
    dedup table is unbounded state that has to be managed, and managing it is what
    creates the hazard below.

PRUNING REOPENS THE WINDOW THE TABLE EXISTS TO CLOSE

    The record table grows forever, so it must be pruned. But an event older than
    the prune horizon has no record, and replaying it applies the effect again with
    nothing left to stop it.

    So the prune horizon and the maximum replay depth are **one constraint wearing
    two names**, and nothing enforces the relationship unless somebody writes it
    down. `replay` refuses to cross the horizon rather than discovering the problem
    by double-applying, and the refusal names both numbers so the person who set
    them can see they disagree.

ORDERING IS PER KEY, AND TIMESTAMPS ARE NOT A TOTAL ORDER

    `EVENT_CONTRACTS` §3: only per-trip order is guaranteed. A consumer that sorts
    the whole stream by `occurred_at` gets a plausible sequence with no meaning
    across aggregates.

    And within one key, two events can share a timestamp — clocks have resolution.
    Sorting by `occurred_at` alone is therefore not deterministic either, so the sort
    breaks ties on `event_id`. That buys **reproducibility, not causality**: two
    replays agree with each other, and neither can tell you which event really came
    first. Recording the difference matters more than hiding it.

UNKNOWN FIELDS ARE IGNORED, NEVER FATAL

    `EVENT_CONTRACTS` §3: "Tolerate additive schema changes." A producer adding a
    field must not break every consumer at once — which is what strict parsing does,
    at the moment of a deploy that looked additive.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from outbox import Envelope, OutboxError


class ConsumerError(RuntimeError):
    """A consumer or replay rule was violated. No effect was applied."""


class ReplayBeyondHorizonError(ConsumerError):
    """The replay reaches further back than the idempotency records survive."""


def envelope_from_wire(raw: dict[str, Any]) -> Envelope:
    """Build an envelope from a wire payload, ignoring fields we do not know.

    Additive tolerance is a delivery property, not a nicety: a producer adding one
    optional field would otherwise break every consumer simultaneously, during a
    deploy whose change log said "additive".
    """
    required = (
        "event_id",
        "event_type",
        "occurred_at",
        "recorded_at",
        "tenant_id",
        "correlation_id",
        "schema_version",
    )
    missing = [name for name in required if name not in raw]
    if missing:
        raise ConsumerError(f"envelope is missing required field(s): {', '.join(missing)}")
    return Envelope(
        event_id=str(raw["event_id"]),
        event_type=str(raw["event_type"]),
        occurred_at=raw["occurred_at"],
        recorded_at=raw["recorded_at"],
        tenant_id=str(raw["tenant_id"]),
        correlation_id=str(raw["correlation_id"]),
        actor=raw.get("actor"),
        schema_version=int(raw["schema_version"]),
        payload_ids=dict(raw.get("payload_ids") or {}),
    )


def in_key_order(envelopes: Iterable[Envelope]) -> list[Envelope]:
    """Deterministic order within each key. **Not** a causal order.

    Ties on `occurred_at` are broken by `event_id` so two replays agree with each
    other. That is reproducibility; it is not a claim about which event happened
    first, and the two are easy to confuse because the output looks identical.
    """
    return sorted(envelopes, key=lambda e: (e.occurred_at, e.event_id))


@dataclass
class ProcessedLog:
    """Which events a consumer has already applied.

    In memory here; `processed_events` is the table it stands for. The rules worth
    testing are the horizon interaction and the per-consumer keying, and both are
    properties of the logic rather than of the storage.
    """

    _seen: dict[tuple[str, str], datetime] = field(default_factory=dict)
    _horizon: dict[str, datetime] = field(default_factory=dict)

    def record(self, consumer: str, envelope: Envelope) -> None:
        self._seen[(consumer, envelope.event_id)] = envelope.occurred_at

    def has_seen(self, consumer: str, event_id: str) -> bool:
        return (consumer, event_id) in self._seen

    def prune_before(self, consumer: str, moment: datetime) -> int:
        """Discard old records and raise the replay floor by the same movement.

        The horizon is set here rather than by a separate call on purpose: a prune
        that does not move the horizon leaves a replay believing it is protected by
        records that no longer exist.
        """
        if moment.tzinfo is None:
            raise ConsumerError("a prune horizon must be timezone-aware")
        removed = [k for k, at in self._seen.items() if k[0] == consumer and at < moment]
        for key in removed:
            del self._seen[key]
        existing = self._horizon.get(consumer)
        self._horizon[consumer] = max(existing, moment) if existing else moment
        return len(removed)

    def horizon(self, consumer: str) -> datetime | None:
        return self._horizon.get(consumer)


@dataclass
class IdempotentConsumer:
    """Applies each event once in effect, however many times it is delivered."""

    name: str
    handler: Callable[[Envelope], None]
    log: ProcessedLog
    #: Set when repeating the effect is harmless — `SET status = 'confirmed'` and
    #: the like. A naturally idempotent handler needs no record, so it costs no
    #: unbounded table and creates no prune hazard.
    naturally_idempotent: bool = False
    applied: int = 0
    skipped: int = 0

    def handle(self, envelope: Envelope) -> bool:
        """Apply the effect if it has not been applied. Returns whether it ran.

        The record and the effect belong to one transaction. Here that is expressed
        by recording immediately after the handler returns and not at all if it
        raises: a handler that fails must be retried, and a record written before a
        failure would suppress the retry for ever.
        """
        if not self.naturally_idempotent and self.log.has_seen(self.name, envelope.event_id):
            self.skipped += 1
            return False
        self.handler(envelope)
        if not self.naturally_idempotent:
            self.log.record(self.name, envelope)
        self.applied += 1
        return True

    def consume(self, envelopes: Sequence[Envelope]) -> int:
        """Handle a batch in per-key order. Returns how many effects ran."""
        return sum(1 for envelope in in_key_order(envelopes) if self.handle(envelope))


def replay(
    consumer: IdempotentConsumer,
    envelopes: Sequence[Envelope],
    *,
    since: datetime,
) -> int:
    """Reprocess a range, or refuse because the records that make it safe are gone.

    The refusal is the point. Replaying past the prune horizon re-applies effects
    with nothing left to deduplicate them, and the symptom is duplicated work
    somewhere downstream long after the replay finished — so it fails here, naming
    both dates, where the person who chose them can see that they disagree.
    """
    if since.tzinfo is None:
        raise ConsumerError("a replay start must be timezone-aware")
    horizon = consumer.log.horizon(consumer.name)
    if horizon is not None and since < horizon and not consumer.naturally_idempotent:
        raise ReplayBeyondHorizonError(
            f"replay from {since.isoformat()} reaches past the prune horizon "
            f"{horizon.isoformat()} for consumer {consumer.name!r}. The idempotency "
            f"records before that point are gone, so this replay would apply effects "
            f"a second time. Either shorten the replay or stop pruning so aggressively "
            f"— the two numbers are one policy"
        )
    return consumer.consume([e for e in envelopes if e.occurred_at >= since])


def group_by_key(
    envelopes: Iterable[Envelope], *, key: str = "trip_id"
) -> dict[str, list[Envelope]]:
    """Partition by order key, because ordering means nothing across keys.

    A consumer handed the whole stream will sort it and believe the result. Handing
    it groups makes the guarantee visible in the shape of the data.
    """
    grouped: dict[str, list[Envelope]] = {}
    for envelope in envelopes:
        grouped.setdefault(envelope.payload_ids.get(key, ""), []).append(envelope)
    return {k: in_key_order(v) for k, v in grouped.items()}


__all__ = [
    "ConsumerError",
    "Envelope",
    "IdempotentConsumer",
    "OutboxError",
    "ProcessedLog",
    "ReplayBeyondHorizonError",
    "envelope_from_wire",
    "group_by_key",
    "in_key_order",
    "replay",
]
