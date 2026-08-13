"""Credential retrieval with rotation — STEP-005.01 (REQ-DATA-002, REQ-SEC-003).

ROTATION MEANS "WITHOUT A RESTART", WHICH MEANS NEVER CACHING FOREVER
    The sub-step's §4 flags exactly this as the thing to verify: *"whether the
    chosen secret manager supports rotation without restart"*.

    That question cannot be answered yet — `DEC-007` has not chosen a cloud
    provider, so there is no secret manager to test. What CAN be settled now is the
    shape that makes rotation possible at all, and the shape is the part a vendor
    choice does not change: **fetch through a port, cache with a TTL, never hold a
    credential in a module-level constant.**

    A credential read once at import is a credential that survives rotation, and
    the symptom is 401s an hour after a rotation nobody connected to the outage.

WHY THE SECRET NEVER GETS A __str__
    `Secret` deliberately has no readable representation. The single most common
    way a credential reaches a log is an f-string in an error path written by
    someone who was debugging something else. Making the value unavailable to
    formatting costs nothing and removes the whole class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class CredentialError(Exception):
    """A credential could not be obtained."""


class Secret:
    """A credential that refuses to render itself.

    `str(secret)`, `repr(secret)` and f-strings all produce a placeholder. The value
    comes out only via `reveal()`, which is greppable — so "where does this
    credential get used" is a search rather than an audit.
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        if not value:
            raise CredentialError("refusing to construct an empty Secret")
        self._value = value

    def reveal(self) -> str:
        """The actual value. Call this as late as possible and never store the result."""
        return self._value

    def __str__(self) -> str:  # pragma: no cover - trivial, but load-bearing
        return "<Secret: redacted>"

    __repr__ = __str__

    def __format__(self, spec: str) -> str:
        return "<Secret: redacted>"


class SecretSource(Protocol):
    """Where secrets come from. One method, so a vendor SDK is a small adapter."""

    def fetch(self, name: str) -> str: ...


@dataclass
class RotatingCredential:
    """A credential re-fetched when its TTL expires.

    The TTL is short by default (five minutes) because the cost of being wrong in
    each direction is asymmetric: a needless fetch is one call to a secret manager,
    while a stale credential is an outage that looks like a provider problem.
    """

    name: str
    source: SecretSource
    ttl_seconds: float = 300.0
    _cached: Secret | None = field(default=None, init=False)
    _fetched_at: float | None = field(default=None, init=False)

    def get(self, now: float) -> Secret:
        if (
            self._cached is None
            or self._fetched_at is None
            or (now - self._fetched_at) >= self.ttl_seconds
        ):
            try:
                value = self.source.fetch(self.name)
            except Exception as exc:
                raise CredentialError(f"could not fetch credential {self.name!r}: {exc}") from exc
            self._cached = Secret(value)
            self._fetched_at = now
        return self._cached

    def invalidate(self) -> None:
        """Force a re-fetch on the next `get`.

        Called on a 401 so a rotation that happened mid-TTL is picked up on the
        retry instead of after the cache expires. Without this, rotation "works"
        but with an outage window as long as the TTL.
        """
        self._cached = None
        self._fetched_at = None
