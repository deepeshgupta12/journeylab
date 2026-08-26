"""Transactional outbox relay — STEP-006.06 (REQ-DATA-008, REQ-NFR-005).

A RETRY CAP PROTECTS AGAINST A POISON MESSAGE, NOT AGAINST AN OUTAGE

    This is the decision that shapes the module, and the obvious implementation
    gets it wrong.

    The obvious relay counts attempts per message and dead-letters at five. Now the
    broker goes down for twenty minutes. Every message fails, every message burns
    its five attempts within a minute or two of backoff, and the entire backlog
    lands in the dead-letter queue — where a human has to replay it, having lost
    ordering, while the broker was never broken and came back on its own.

    A poison message and an outage look identical one message at a time, and they
    need opposite responses:

      poison   -> one message fails while its neighbours succeed. Dead-letter it,
                  or it blocks the queue forever.
      outage   -> everything fails at once. Keep retrying and alert; dead-lettering
                  converts a transient failure into permanent manual work.

    So `should_dead_letter` takes the **batch outcome** as well as the message. If
    nothing in the batch succeeded, nothing is dead-lettered however many attempts
    it has. A message only becomes poison once it can be seen failing on its own.

LAG IS MEASURED FROM WHEN THE FACT HAPPENED, NOT FROM THE LAST ATTEMPT

    A relay that died an hour ago has, by its own reckoning, zero time since its
    last attempt — the metric it would naturally publish is the one that looks
    healthiest exactly when it is most wrong. `oldest_pending_age` measures from
    `occurred_at`, so a stalled relay's lag grows on its own.

    Same shape as measuring freshness from ingestion time instead of observation
    time (STEP-005.08): the convenient clock is the one that hides the failure.

AT-LEAST-ONCE MEANS DUPLICATES ARE CERTAIN, NOT POSSIBLE

    The relay marks a row published *after* the broker accepts it. A crash in
    between re-sends. That is the correct trade — the alternative marks first and
    loses events — and it is why `.07` exists. No effort is spent here trying to be
    exactly-once, because the attempt would only make the duplicate rarer and
    therefore less tested.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class OutboxError(RuntimeError):
    """A relay operation was refused. Nothing was marked."""


class Status(enum.StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    ACKNOWLEDGED = "acknowledged"
    DEAD_LETTER = "dead_letter"


#: Attempts before a message is *eligible* for the dead-letter queue. Eligibility
#: is not sufficient — see `should_dead_letter`. Provisional pending `DEC-005`.
MAX_ATTEMPTS = 5

#: Backoff is capped so a long outage does not push the next attempt beyond the
#: point anybody is still watching.
BASE_BACKOFF = timedelta(seconds=1)
MAX_BACKOFF = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class Envelope:
    """What the relay publishes. Matches `components.schemas.Envelope`.

    `payload_ids` rather than a payload: `EVENT_CONTRACTS` §2 permits IDs and
    classifications only. An event stream carrying trip content is a store that
    `REQ-PRIV-006` deletion would have to traverse, and it is the one store nobody
    thinks of as a store.
    """

    event_id: str
    event_type: str
    occurred_at: datetime
    recorded_at: datetime
    tenant_id: str
    correlation_id: str
    actor: str | None
    schema_version: int
    payload_ids: dict[str, str]

    def __post_init__(self) -> None:
        for label, moment in (("occurred_at", self.occurred_at), ("recorded_at", self.recorded_at)):
            if moment.tzinfo is None:
                raise OutboxError(f"{label} must be timezone-aware")
        if not self.tenant_id.strip():
            raise OutboxError(
                "every event carries a tenant (REQ-SEC-001). An untenanted event is "
                "one a consumer cannot scope, so it either drops it or leaks it"
            )
        if not self.event_type.startswith("journey."):
            raise OutboxError(f"unexpected event type {self.event_type!r}")


@dataclass(frozen=True, slots=True)
class OutboxRow:
    """One queued event and its delivery state."""

    envelope: Envelope
    order_key: str
    status: Status = Status.PENDING
    attempts: int = 0
    last_error: str | None = None

    @property
    def eligible_for_dead_letter(self) -> bool:
        """Eligible, not condemned. `should_dead_letter` decides."""
        return self.attempts >= MAX_ATTEMPTS


def backoff_for(attempt: int) -> timedelta:
    """Capped exponential backoff. Attempt 1 waits the base delay."""
    if attempt < 1:
        raise OutboxError("attempts are counted from 1")
    delay: timedelta = BASE_BACKOFF * (2 ** (attempt - 1))
    return min(delay, MAX_BACKOFF)


@dataclass(frozen=True, slots=True)
class BatchOutcome:
    """What a whole relay pass did, which is what distinguishes poison from outage."""

    published: int
    failed: int

    @property
    def total(self) -> int:
        return self.published + self.failed

    @property
    def looks_like_an_outage(self) -> bool:
        """Nothing got through. One failure among successes is a message problem;
        everything failing at once is an infrastructure problem, and they need
        opposite responses."""
        return self.total > 0 and self.published == 0


def should_dead_letter(row: OutboxRow, outcome: BatchOutcome) -> bool:
    """Whether this message has earned the dead-letter queue.

    Two conditions, and the second is the one the obvious implementation omits:
    the message must have exhausted its attempts **and** its neighbours must be
    getting through. During an outage nothing is dead-lettered, however many
    attempts it has burned, because dead-lettering a transient failure converts it
    into permanent manual work with the ordering lost.
    """
    if not row.eligible_for_dead_letter:
        return False
    return not outcome.looks_like_an_outage


@dataclass(frozen=True, slots=True)
class DeadLetter:
    """A message set aside, with everything needed to replay it.

    The full envelope is kept. A dead-letter queue that stores an error and a
    message id is a record that something failed, not a message — and you
    dead-letter precisely so it can be sent again once the cause is fixed.
    """

    envelope: Envelope
    order_key: str
    attempts: int
    reason: str
    at: datetime

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise OutboxError(
                "a dead letter records why. Without a reason it cannot be triaged, "
                "which makes it the same as a message nobody kept"
            )


class Publisher:
    """The broker, behind a port.

    `DEC-009` chose Kafka (`ADR-015`) and no broker exists yet. The AsyncAPI
    contract is identical either way (STEP-006 §23), so the relay is written against
    the contract and not against a client library.
    """

    def publish(self, envelope: Envelope) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class Relay:
    """One relay pass over a batch of pending rows."""

    publisher: Publisher
    _dead_letters: list[DeadLetter] = field(default_factory=list)

    def run(
        self, rows: Sequence[OutboxRow], *, now: datetime
    ) -> tuple[BatchOutcome, list[OutboxRow]]:
        """Publish what can be published; return the outcome and the updated rows.

        Two passes rather than one, deliberately. The dead-letter decision needs the
        whole batch's outcome, and a single pass would have to decide the first
        message's fate before knowing whether the second one succeeds — which is
        exactly the information that separates poison from outage.
        """
        published: list[OutboxRow] = []
        failed: list[tuple[OutboxRow, str]] = []

        for row in rows:
            if row.status is not Status.PENDING:
                raise OutboxError(
                    f"{row.envelope.event_id} is {row.status}, not pending. Re-publishing "
                    f"a delivered row is a duplicate the relay chose, not one the "
                    f"transport caused"
                )
            try:
                self.publisher.publish(row.envelope)
            except Exception as exc:
                failed.append((row, f"{type(exc).__name__}: {exc}"))
            else:
                published.append(row)

        outcome = BatchOutcome(published=len(published), failed=len(failed))
        updated: list[OutboxRow] = [
            # Marked published only after the broker accepted it. A crash between
            # the send and this line re-sends, which is the at-least-once trade.
            OutboxRow(
                envelope=row.envelope,
                order_key=row.order_key,
                status=Status.PUBLISHED,
                attempts=row.attempts + 1,
            )
            for row in published
        ]

        for row, error in failed:
            attempted = OutboxRow(
                envelope=row.envelope,
                order_key=row.order_key,
                status=Status.PENDING,
                attempts=row.attempts + 1,
                last_error=error,
            )
            if should_dead_letter(attempted, outcome):
                self._dead_letters.append(
                    DeadLetter(
                        envelope=row.envelope,
                        order_key=row.order_key,
                        attempts=attempted.attempts,
                        reason=error,
                        at=now,
                    )
                )
                updated.append(
                    OutboxRow(
                        envelope=row.envelope,
                        order_key=row.order_key,
                        status=Status.DEAD_LETTER,
                        attempts=attempted.attempts,
                        last_error=error,
                    )
                )
            else:
                updated.append(attempted)

        return outcome, updated

    def dead_letters(self) -> tuple[DeadLetter, ...]:
        return tuple(self._dead_letters)


def oldest_pending_age(rows: Sequence[OutboxRow], *, now: datetime) -> timedelta:
    """Lag for `ALRT-QUEUE-001`, measured from when the fact happened.

    Not from the last attempt. A relay that died an hour ago has zero time since its
    last attempt, so that metric reads healthiest exactly when it is most wrong.
    """
    pending = [r for r in rows if r.status is Status.PENDING]
    if not pending:
        return timedelta(0)
    return now - min(r.envelope.occurred_at for r in pending)


def dead_letter_depth(rows: Sequence[OutboxRow]) -> int:
    return sum(1 for r in rows if r.status is Status.DEAD_LETTER)
