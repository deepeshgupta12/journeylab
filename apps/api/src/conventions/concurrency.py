"""Idempotency and optimistic concurrency — STEP-004.01 (REQ-PLAT-005).

TWO MECHANISMS THAT ARE CONSTANTLY CONFUSED
    They answer different questions and this module keeps them apart:

      `Idempotency-Key`  "Is this the same request I already handled?"
                         Protects against a client retrying after a timeout,
                         where the first attempt may well have succeeded.

      `ETag` / `If-Match` "Is the resource still in the state you read?"
                         Protects against two editors overwriting each other.

    A command needs both. Idempotency alone lets a stale editor clobber a newer
    version; ETags alone let a network retry create two trips.

WHY IDEMPOTENCY IS REQUIRED, NOT OFFERED
    `API_CONTRACTS.md` §1: "`Idempotency-Key` **required** on every state-changing
    command". Optional idempotency is idempotency nobody uses until after the
    duplicate-charge incident. `require_idempotency_key` raises when it is absent,
    so an operation cannot forget.

THE REPLAY RULE, AND THE TRAP IN IT
    A repeated key with the **same** request returns the original result. A
    repeated key with a **different** request is a client defect and returns 409 —
    `ERROR_MODEL.md` calls it exactly that: "Surface as a client defect."

    The trap is that "same request" has to mean something precise. Comparing raw
    bodies makes two semantically identical requests differ over key order or
    whitespace; comparing parsed bodies makes `{"a": 1}` and `{"a": 1.0}` the
    same. This module hashes a canonical JSON form — sorted keys, no insignificant
    whitespace — and states that choice rather than leaving it to each handler.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Final, NamedTuple

IDEMPOTENCY_HEADER: Final = "Idempotency-Key"
CORRELATION_HEADER: Final = "X-Correlation-Id"

#: How long a key is honoured. Beyond this the same key is a new request.
#:
#: 24 hours because that is longer than any client's retry budget and shorter
#: than a human deciding to "try that again tomorrow" — which is a new intent,
#: not a retry, and must not silently return yesterday's result.
IDEMPOTENCY_TTL_SECONDS: Final = 24 * 60 * 60

#: A key is client-generated, so its shape is validated but its content is not
#: trusted. Length-capped because it becomes a cache key.
_KEY_SHAPE: Final = re.compile(r"^[A-Za-z0-9._:\-]{8,255}$")


class IdempotencyError(ValueError):
    """Raised when a key is missing or malformed."""


class IdempotencyConflictError(Exception):
    """A known key was reused with a different request body."""


class ConcurrencyConflictError(Exception):
    """`If-Match` did not match the current version."""


class RequestFingerprint(NamedTuple):
    """What makes two attempts "the same request"."""

    key: str
    digest: str


def require_idempotency_key(headers: dict[str, str]) -> str:
    """Extract and validate the key, or raise.

    Header lookup is case-insensitive because HTTP header names are, and a
    dictionary lookup is not — a client sending `idempotency-key` is correct and
    a handler that misses it would create duplicates.
    """
    value = _header(headers, IDEMPOTENCY_HEADER)
    if value is None or value.strip() == "":
        raise IdempotencyError(
            f"{IDEMPOTENCY_HEADER} is required on every state-changing command. "
            f"Generate one per user intent — a UUID is fine — and reuse it for "
            f"every retry of that same intent."
        )
    key = value.strip()
    if not _KEY_SHAPE.match(key):
        raise IdempotencyError(f"{IDEMPOTENCY_HEADER} must be 8-255 characters of [A-Za-z0-9._:-]")
    return key


def _header(headers: dict[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def fingerprint(key: str, body: Any) -> RequestFingerprint:
    """Canonical digest of a request, for replay comparison.

    Canonical JSON: sorted keys, compact separators. So `{"b":1,"a":2}` and
    `{"a":2,"b":1}` are the same request — they are — while `{"a":1}` and
    `{"a":"1"}` are not, because a string and a number mean different things to
    whatever validates them next.
    """
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return RequestFingerprint(key=key, digest=digest)


def check_replay(stored: RequestFingerprint | None, incoming: RequestFingerprint) -> bool:
    """Decide what a repeated key means.

    Returns True when this is a genuine replay whose original result should be
    returned. Raises `IdempotencyConflictError` when the key was reused with a
    different body.

    Returning False means "not seen before — process it".
    """
    if stored is None:
        return False
    if stored.key != incoming.key:
        # Programming error in the caller: it looked up the wrong record.
        raise IdempotencyError("fingerprint key mismatch — wrong record looked up")
    if stored.digest != incoming.digest:
        raise IdempotencyConflictError(
            "this Idempotency-Key was already used with a different request body"
        )
    return True


# --- optimistic concurrency ---------------------------------------------------


def etag_for(version: int | str, resource_id: str) -> str:
    """A strong ETag for a resource version.

    Strong, not weak (`W/`): `If-Match` requires strong comparison, and a weak tag
    would make the precondition succeed for representations that are equivalent
    but not identical — which is precisely the case a lost-update check must
    reject.

    Derived from the version and the id together, so an ETag from one resource
    cannot satisfy a precondition on another.
    """
    material = f"{resource_id}:{version}".encode()
    return '"' + hashlib.sha256(material).hexdigest()[:32] + '"'


def require_if_match(headers: dict[str, str], current_etag: str) -> None:
    """Enforce `If-Match` on a mutating request.

    A **missing** `If-Match` is refused, not treated as "no opinion". RFC 9110
    allows a server to require it, and here the whole point is that an editor
    states which version they are replacing. Treating absence as consent is how a
    lost update happens on the very first request that forgets the header.

    `*` is accepted: it means "any current representation", which is a deliberate
    statement that the caller intends to overwrite whatever is there.
    """
    provided = _header(headers, "If-Match")
    if provided is None or provided.strip() == "":
        raise ConcurrencyConflictError(
            "If-Match is required on this operation. Send the ETag you received "
            "when you read the resource, so a concurrent edit cannot be lost."
        )
    candidates = {tag.strip() for tag in provided.split(",")}
    if "*" in candidates:
        return
    if current_etag not in candidates:
        raise ConcurrencyConflictError(
            "the resource changed since you read it. Refetch, review the "
            "difference, and re-apply your change."
        )


def correlation_id(headers: dict[str, str]) -> str:
    """The correlation ID for this request, accepted from the client or minted.

    Accepted from `X-Correlation-Id` so a caller can tie its own logs to ours, and
    **length-capped and shape-checked** because it is echoed into responses and
    written to logs. An unbounded client-controlled string that reaches a log is a
    log-injection primitive.

    Anything unusable is replaced rather than rejected: a bad correlation header
    should not fail a request that is otherwise fine.
    """
    provided = _header(headers, CORRELATION_HEADER)
    if provided is not None:
        candidate = provided.strip()
        if re.fullmatch(r"[A-Za-z0-9._:\-]{8,128}", candidate):
            return candidate
    return f"corr_{uuid.uuid4().hex}"
