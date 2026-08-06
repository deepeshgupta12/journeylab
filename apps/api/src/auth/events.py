"""Stamping tenant onto event envelopes — STEP-002.02.

SCOPE HONESTY
    The sub-step asks for `tenant_id` on "every emitted event envelope". There is
    no event system yet — the outbox arrives at STEP-006 (and DEC-009, the event
    backbone, is still open). So this module provides the stamping primitive and
    proves it; it cannot enforce that every emitter uses it, because there are no
    emitters.

    The enforcement point — an outbox writer that refuses an unstamped envelope —
    belongs to STEP-006. Recorded as a carried gap in BR-011 rather than implied to
    be finished here.

REQ-SEC-001.
"""

from __future__ import annotations

from typing import Any

from .context import RequestContext

_TENANT_FIELD = "tenant_id"
_ACTOR_FIELD = "actor_id"


def stamp_envelope(envelope: dict[str, Any], context: RequestContext) -> dict[str, Any]:
    """Return a copy of `envelope` carrying tenant and actor.

    Returns a new dict rather than mutating. An event envelope is frequently built
    once and emitted more than once; in-place mutation makes the stamp order-
    dependent, and a stamp that depends on call order is a stamp that will
    eventually be missing.

    Refuses to overwrite a conflicting existing tenant: if some caller has already
    put a different `tenant_id` on the envelope, that is a bug worth surfacing, not
    silently correcting.
    """
    existing = envelope.get(_TENANT_FIELD)
    if existing is not None and str(existing) != str(context.organization_id):
        raise ValueError("envelope already carries a different tenant_id")

    return {
        **envelope,
        _TENANT_FIELD: str(context.organization_id),
        _ACTOR_FIELD: str(context.actor_id),
    }
