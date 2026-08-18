"""Signed callback receipt — STEP-005.06 (REQ-BOOK-002, TST-BOOK-002).

VERIFY BEFORE PARSE IS AN ORDERING, NOT A STEP

    §5: "**Verify webhook signature before parsing the body.**"

    Almost every implementation gets this backwards, and it does not look
    backwards. The natural shape is:

        body = json.loads(request.body)      # <- the parser has now run
        verify(body["signature"], body)      #    on unauthenticated input

    By the time the signature is checked, a JSON parser has already consumed
    attacker-controlled bytes. That is the whole attack surface the signature was
    supposed to stand in front of.

    So this module's entry point takes **raw bytes** and returns a parsed payload
    only after the HMAC matches. There is deliberately no function here that
    verifies a signature against an already-parsed object, because such a function
    would be the thing everyone reaches for.

WHY THE SIGNATURE IS OVER THE EXACT BYTES RECEIVED
    Re-serialising a parsed body produces different bytes — different key order,
    different whitespace, different float formatting — and the signature will not
    match. Implementations that hit this usually "fix" it by canonicalising, which
    quietly reintroduces parse-before-verify. The raw bytes are the message.

WHY THE TIMESTAMP MUST BE INSIDE THE SIGNED MATERIAL
    A replay window checked against a timestamp the attacker can edit is not a
    replay window. The timestamp is signed alongside the body, so moving it
    invalidates the signature — which is why `verify_and_parse` takes it as a
    separate argument rather than reading it out of the payload it has not yet
    trusted.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any


class WebhookRejectedError(Exception):
    """A callback was refused. Deliberately one type for every reason.

    A caller must not be able to branch on *why* verification failed, and an
    attacker must not learn it from a response. Bad signature, stale timestamp and
    malformed body are indistinguishable from outside — the same reasoning as the
    opaque denial in `auth/errors.py`.
    """


#: How old a callback may be. Five minutes is long enough to survive a retry and a
#: clock skew, short enough that a captured request is not useful tomorrow.
DEFAULT_REPLAY_WINDOW = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class VerifiedCallback:
    """A callback whose signature matched, and the payload it carried."""

    event_id: str
    payload: dict[str, Any]
    signed_at: datetime


def expected_signature(raw_body: bytes, signed_at: datetime, secret: str) -> str:
    """HMAC-SHA256 over timestamp and body together.

    The timestamp is inside the signed material, not beside it. Signing only the
    body would let an attacker replay a captured request forever by adjusting the
    timestamp header, which is a replay window that stops nothing.
    """
    if not secret:
        raise WebhookRejectedError("refusing to verify against an empty secret")
    material = f"{int(signed_at.timestamp())}.".encode() + raw_body
    return hmac.new(secret.encode(), material, hashlib.sha256).hexdigest()


def verify_and_parse(
    raw_body: bytes,
    *,
    signature: str,
    signed_at: datetime,
    secret: str,
    now: datetime,
    replay_window: timedelta = DEFAULT_REPLAY_WINDOW,
) -> VerifiedCallback:
    """Authenticate, then parse. Never the other way round.

    Takes `bytes` rather than a parsed object on purpose: the type makes the
    ordering impossible to get wrong, because there is nothing parsed to pass in.
    """
    if signed_at.tzinfo is None or now.tzinfo is None:
        raise WebhookRejectedError("timestamps must be timezone-aware")

    # 1. Freshness, before any cryptography. A stale request is discarded without
    #    spending an HMAC on it, and before the body is looked at in any way.
    age = now - signed_at
    if age > replay_window:
        raise WebhookRejectedError("callback rejected")
    if age < -replay_window:
        # Future-dated beyond tolerable skew. Accepting it would let an attacker
        # mint a request that stays valid for as long as they chose.
        raise WebhookRejectedError("callback rejected")

    # 2. Signature over the RAW BYTES. Nothing has parsed them yet.
    expected = expected_signature(raw_body, signed_at, secret)
    if not hmac.compare_digest(expected, signature):
        # Constant time: a byte-by-byte comparison leaks the correct prefix, and a
        # signature is guessable one byte at a time if comparison is not constant.
        raise WebhookRejectedError("callback rejected")

    # 3. ONLY NOW is the body parsed.
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise WebhookRejectedError("callback rejected") from exc

    if not isinstance(payload, dict):
        raise WebhookRejectedError("callback rejected")

    event_id = payload.get("event_id")
    if not isinstance(event_id, str) or not event_id.strip():
        raise WebhookRejectedError("callback rejected")

    return VerifiedCallback(event_id=event_id, payload=payload, signed_at=signed_at)


@dataclass
class SeenEvents:
    """Idempotent receipt within the replay window.

    THE TENSION THIS RESOLVES
        Replay protection rejects requests that are OLD. Idempotency accepts
        requests that are DUPLICATE. §5 asks for both, and they pull in opposite
        directions: a partner retrying after a timeout sends the same event again,
        legitimately, and must not be treated as an attack.

        So a duplicate inside the window is accepted and reported as already
        handled — not refused. A duplicate outside the window never reaches here,
        because `verify_and_parse` rejected it on age first.
    """

    window: timedelta = DEFAULT_REPLAY_WINDOW
    _seen: dict[str, datetime] = field(default_factory=dict)

    def record(self, event_id: str, now: datetime) -> bool:
        """True when this is the first time. False when it is a legitimate retry."""
        self._prune(now)
        if event_id in self._seen:
            return False
        self._seen[event_id] = now
        return True

    def _prune(self, now: datetime) -> None:
        # Bounded by the window, so the set cannot grow without limit — an
        # unbounded seen-set is a memory exhaustion primitive for anyone who can
        # send signed callbacks.
        cutoff = now - self.window
        for event_id in [k for k, seen in self._seen.items() if seen < cutoff]:
            del self._seen[event_id]


def now_utc() -> datetime:
    return datetime.now(UTC)
