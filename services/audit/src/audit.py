"""Audit event writer — STEP-002.07 (REQ-SEC-007).

This is the sink the earlier sub-steps were writing towards. `provisioning`
returns an `AuditRecord` and `authz.authorize` returns `Decision.audit`; neither
had anywhere to go. They do now.

WHAT MAKES THIS AN AUDIT TRAIL RATHER THAN A LOG
    1. **Append-only, enforced by the database.** `journeylab_app` holds INSERT and
       SELECT on `audit_events` and nothing else (migration 002). There is no
       update or delete function in this module — and if someone wrote one, the
       database would refuse it.
    2. **Separate from application logs.** Its own table, its own schema, its own
       retention. An audit trail interleaved with debug output is not evidence.
    3. **Redacted at emission.** See `redaction.py`. A redaction failure blocks the
       write rather than leaking, which matters more here than anywhere else:
       the store is append-only, so a leaked secret could not be removed.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from redaction import RedactionError, redact

Outcome = Literal["allowed", "denied", "error"]


class AuditWriteError(Exception):
    """Raised when an audit event could not be written.

    Deliberately NOT swallowed by the writer. §8: "a silent audit failure is a
    compliance gap." The caller decides whether losing the event is acceptable;
    this module refuses to make that decision quietly on their behalf.
    """


class _Cursor(Protocol):
    async def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...
    async def fetchone(self) -> tuple[object, ...] | None: ...


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One thing that happened, and who did it.

    `action` follows `noun.verb` (`membership.revoked`), matched by a CHECK
    constraint in migration 002 so a typo fails at the write rather than producing
    an un-queryable trail.
    """

    action: str
    subject: str
    outcome: Outcome
    occurred_at: datetime
    organization_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None
    correlation_id: str | None = None
    payload: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            # A naive timestamp has no defined instant. In an audit trail that is
            # not a formatting nit: it makes ordering across regions unreliable,
            # and ordering is most of what an investigation depends on.
            raise ValueError(f"{self.action}: occurred_at must be timezone-aware")


async def emit(cur: _Cursor, event: AuditEvent) -> uuid.UUID:
    """Write one audit event. Returns its id.

    Raises `RedactionError` if the payload cannot be safely redacted — the event
    is then NOT written — and `AuditWriteError` if the insert itself fails.
    """
    try:
        payload = redact(event.payload or {})
    except RedactionError:
        # Re-raised unchanged. The caller must see that redaction, specifically,
        # is why nothing was recorded.
        raise

    try:
        await cur.execute(
            """
            INSERT INTO audit_events
                (organization_id, actor_id, action, subject, outcome, correlation_id,
                 payload, occurred_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            RETURNING id
            """,
            (
                str(event.organization_id) if event.organization_id else None,
                str(event.actor_id) if event.actor_id else None,
                event.action,
                event.subject,
                event.outcome,
                event.correlation_id,
                json.dumps(payload),
                event.occurred_at,
            ),
        )
    except Exception as exc:
        # Any failure to write is surfaced. Catching narrowly would let an
        # unanticipated driver error pass as success, which is the exact silent
        # gap §8 warns about.
        raise AuditWriteError(f"failed to write audit event {event.action!r}: {exc}") from exc

    row = await cur.fetchone()
    if row is None:  # pragma: no cover - RETURNING always yields a row
        raise AuditWriteError(f"audit event {event.action!r} produced no id")
    return uuid.UUID(str(row[0]))


def from_decision(
    *,
    action: str,
    subject: str,
    allowed: bool,
    organization_id: uuid.UUID | None,
    actor_id: uuid.UUID | None,
    reason: str,
    correlation_id: str | None = None,
) -> AuditEvent:
    """Build an event from an authorization decision.

    The denial `reason` belongs here and NOWHERE ELSE. `auth/errors.py` keeps it
    out of the response so denial and absence stay indistinguishable; the audit
    trail is the one place the distinction is both safe and necessary.
    """
    return AuditEvent(
        action=action,
        subject=subject,
        outcome="allowed" if allowed else "denied",
        occurred_at=datetime.now(UTC),
        organization_id=organization_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        payload={"reason": reason},
    )
