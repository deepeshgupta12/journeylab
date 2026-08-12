"""Session store and revocation — STEP-002.08 (REQ-SEC-003, REQ-SEC-001, REQ-PRIV-001).

WHAT THIS FIXES
    STEP-002.05 built the session decision logic as pure functions taking a record
    as a parameter, and the record had nowhere to live. `signOutCookies()` in
    `apps/web/src/auth/session.ts` still carries the comment "Server-side
    revocation is authoritative and is what actually ends access" — pointing at
    something that did not exist. This module is that thing (`BUG-022`).

    Without it, signing out cleared cookies and an already-issued token kept
    working until it expired on its own. A cookie is a client-side hint; the only
    thing that ends access is the server refusing it.

THE HASH FORMAT IS A CROSS-LANGUAGE CONTRACT
    Guest tokens are minted in TypeScript (`apps/web/src/auth/guest.ts`) and stored
    here. Both sides must produce byte-identical hashes or every guest session
    fails to validate — and it would fail as `unknown_token`, which is
    indistinguishable from an attacker presenting a forged token, so the cause
    would not be obvious from the symptom.

    The format is SHA-256 then base64url with padding stripped. `test_sessions.py`
    pins it with a vector generated from the TypeScript implementation rather than
    from this one, because a vector generated from the code under test proves only
    that the code agrees with itself.

TWO TABLES, NOT ONE
    `sessions` is tenant-scoped; `guest_sessions` has no tenant because a guest has
    none. Migration 003 and the sub-step's §6 carry the reasoning. The visible cost
    is that revocation has two code paths, which is why each is one small function
    rather than one function with a mode flag.
"""

from __future__ import annotations

import base64
import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

#: Why a session ended. A revocation with no reason cannot distinguish a user
#: signing out from an administrator ending a compromised session, and those call
#: for different responses. Migration 003 enforces that one never appears without
#: the other.
REASON_SIGN_OUT = "sign_out"
REASON_MEMBERSHIP_REVOKED = "membership_revoked"
REASON_ADMIN = "administrative"
REASON_CREDENTIAL_CHANGE = "credential_change"

VALID_REASONS = frozenset(
    {REASON_SIGN_OUT, REASON_MEMBERSHIP_REVOKED, REASON_ADMIN, REASON_CREDENTIAL_CHANGE}
)


class _Cursor(Protocol):
    """The slice of an async DB-API cursor this module uses.

    Structural, matching `provisioning._Cursor`, so ADR-011's driver choice does
    not spread further than it must.
    """

    async def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...
    async def fetchone(self) -> tuple[object, ...] | None: ...
    async def fetchall(self) -> list[tuple[object, ...]]: ...


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """What happened, to be persisted by the caller.

    Deliberately the same shape as `provisioning.AuditRecord` and returned for the
    same reason: handing the obligation back as a value means it cannot be
    forgotten silently.
    """

    action: str
    actor_id: uuid.UUID | None
    organization_id: uuid.UUID | None
    subject: str
    occurred_at: datetime


class SessionError(ValueError):
    """A session operation was asked for something it must refuse."""


def _now() -> datetime:
    return datetime.now(UTC)


def hash_token(token: str) -> str:
    """SHA-256 then unpadded base64url — the format `guest.ts` produces.

    Not a slow KDF, and that is deliberate rather than an oversight: the token is
    256 bits of CSPRNG output, so there is no dictionary to attack and a work
    factor buys nothing but latency on every request.
    """
    if not token:
        raise SessionError("refusing to hash an empty token")
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


@dataclass(frozen=True, slots=True)
class SessionValidity:
    """The outcome of presenting a token.

    `reason` is populated only when invalid, and the reasons are deliberately
    coarse — `revoked` and `expired` are distinguished for the audit trail, but a
    caller must not relay either to the client. Telling a bearer that their token
    is *revoked* rather than merely unknown confirms it once existed.
    """

    valid: bool
    session_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    reason: str | None = None


# --- authenticated sessions ---------------------------------------------------


async def record_session(
    cur: _Cursor,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    token: str,
    expires_at: datetime,
    now: datetime | None = None,
) -> uuid.UUID:
    """Persist a new authenticated session, storing only the token's hash."""
    moment = now or _now()
    if expires_at.tzinfo is None:
        raise SessionError("expires_at must be timezone-aware")
    if expires_at <= moment:
        raise SessionError("refusing to record a session that has already expired")

    await cur.execute(
        "INSERT INTO sessions (organization_id, user_id, token_hash, issued_at, expires_at) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (str(organization_id), str(user_id), hash_token(token), moment, expires_at),
    )
    row = await cur.fetchone()
    if row is None:
        # RLS denies silently by returning no row rather than raising. Treating
        # that as success would hand back a session id that does not exist.
        raise SessionError("session insert returned no row — tenant context not set?")
    return uuid.UUID(str(row[0]))


async def validate_session(
    cur: _Cursor, *, token: str, now: datetime | None = None
) -> SessionValidity:
    """Decide whether a presented token is still usable.

    **Revocation is checked here, which is the entire point of the sub-step.** A
    validator that checks only expiry would let a revoked session run to its
    natural end, and a seven-day guest session revoked on day one would keep
    working for six more.

    The query filters by hash and reads the state back rather than filtering on
    `revoked_at IS NULL`. Both would be secure; this one can tell the audit trail
    *why* a token was refused, and a store that cannot distinguish "revoked" from
    "never existed" cannot answer whether a stolen token was used after sign-out.
    """
    moment = now or _now()
    await cur.execute(
        "SELECT id, user_id, expires_at, revoked_at FROM sessions WHERE token_hash = %s",
        (hash_token(token),),
    )
    row = await cur.fetchone()
    if row is None:
        return SessionValidity(valid=False, reason="unknown_token")

    session_id, user_id, expires_at, revoked_at = row
    if revoked_at is not None:
        return SessionValidity(valid=False, reason="revoked")
    if _as_datetime(expires_at) <= moment:
        return SessionValidity(valid=False, reason="expired")
    return SessionValidity(
        valid=True, session_id=uuid.UUID(str(session_id)), user_id=uuid.UUID(str(user_id))
    )


async def revoke_session(
    cur: _Cursor,
    *,
    organization_id: uuid.UUID,
    session_id: uuid.UUID,
    reason: str,
    actor_id: uuid.UUID | None,
) -> AuditRecord:
    """End one session. Stamps `revoked_at`; the row remains."""
    _check_reason(reason)
    await cur.execute(
        "UPDATE sessions SET revoked_at = now(), revoked_reason = %s "
        "WHERE organization_id = %s AND id = %s AND revoked_at IS NULL",
        (reason, str(organization_id), str(session_id)),
    )
    return AuditRecord(
        action="session.revoked",
        actor_id=actor_id,
        organization_id=organization_id,
        subject=f"session:{session_id}",
        occurred_at=_now(),
    )


async def revoke_all_for_user(
    cur: _Cursor,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    reason: str,
    actor_id: uuid.UUID | None,
) -> AuditRecord:
    """End every live session this user holds **in this organization**.

    Scoped to one organization on purpose. A user may hold memberships in several,
    and revoking a role in one is not a statement about the others — signing a
    contractor out of a client's tenant must not sign them out of their own.
    """
    _check_reason(reason)
    await cur.execute(
        "UPDATE sessions SET revoked_at = now(), revoked_reason = %s "
        "WHERE organization_id = %s AND user_id = %s AND revoked_at IS NULL",
        (reason, str(organization_id), str(user_id)),
    )
    return AuditRecord(
        action="session.revoked_all",
        actor_id=actor_id,
        organization_id=organization_id,
        subject=f"user:{user_id}",
        occurred_at=_now(),
    )


async def live_session_count(
    cur: _Cursor, *, organization_id: uuid.UUID, user_id: uuid.UUID
) -> int:
    """How many sessions are currently in force. Used by tests and by STEP-021."""
    await cur.execute(
        "SELECT count(*) FROM sessions "
        "WHERE organization_id = %s AND user_id = %s AND revoked_at IS NULL",
        (str(organization_id), str(user_id)),
    )
    row = await cur.fetchone()
    return int(str(row[0])) if row else 0


# --- guest sessions -----------------------------------------------------------


async def record_guest_session(
    cur: _Cursor, *, token: str, expires_at: datetime, now: datetime | None = None
) -> uuid.UUID:
    """Persist a guest session. No tenant, by construction (migration 003)."""
    moment = now or _now()
    if expires_at.tzinfo is None:
        raise SessionError("expires_at must be timezone-aware")
    if expires_at <= moment:
        raise SessionError("refusing to record a guest session that has already expired")

    await cur.execute(
        "INSERT INTO guest_sessions (token_hash, issued_at, expires_at) "
        "VALUES (%s, %s, %s) RETURNING id",
        (hash_token(token), moment, expires_at),
    )
    row = await cur.fetchone()
    if row is None:
        raise SessionError("guest session insert returned no row")
    return uuid.UUID(str(row[0]))


async def validate_guest_session(
    cur: _Cursor, *, token: str, now: datetime | None = None
) -> SessionValidity:
    """The server half of `validateGuestSession` in `apps/web/src/auth/guest.ts`.

    The TypeScript function decides validity from a record it is handed; this
    supplies the record and applies the same rules. They agree because the hash
    format is identical — see the module docstring.
    """
    moment = now or _now()
    await cur.execute(
        "SELECT id, expires_at, revoked_at FROM guest_sessions WHERE token_hash = %s",
        (hash_token(token),),
    )
    row = await cur.fetchone()
    if row is None:
        return SessionValidity(valid=False, reason="unknown_token")

    session_id, expires_at, revoked_at = row
    if revoked_at is not None:
        return SessionValidity(valid=False, reason="revoked")
    if _as_datetime(expires_at) <= moment:
        return SessionValidity(valid=False, reason="expired")
    return SessionValidity(valid=True, session_id=uuid.UUID(str(session_id)))


async def revoke_guest_session(cur: _Cursor, *, token: str, reason: str) -> AuditRecord:
    """End a guest session.

    Takes the token rather than an id because the caller signing a guest out holds
    a cookie, not a database row — and looking the id up first would be a second
    round trip that can race with the revocation it is preparing for.
    """
    _check_reason(reason)
    await cur.execute(
        "UPDATE guest_sessions SET revoked_at = now(), revoked_reason = %s "
        "WHERE token_hash = %s AND revoked_at IS NULL",
        (reason, hash_token(token)),
    )
    return AuditRecord(
        action="guest_session.revoked",
        actor_id=None,
        organization_id=None,
        # The token is NOT the subject. An audit row is read by more people than a
        # session store is, and a live bearer token sitting in it would be a
        # credential leak with a retention policy attached.
        subject="guest_session",
        occurred_at=_now(),
    )


# --- helpers ------------------------------------------------------------------


def _check_reason(reason: str) -> None:
    if reason not in VALID_REASONS:
        raise SessionError(
            f"unknown revocation reason {reason!r}. A free-text reason cannot be "
            f"aggregated, so an investigation cannot ask 'how many sessions were "
            f"ended by an administrator last week'. Known: {sorted(VALID_REASONS)}"
        )


def _as_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    raise SessionError(f"expected a datetime from the database, got {type(value).__name__}")
