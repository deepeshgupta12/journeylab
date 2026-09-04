"""The coverage endpoint — STEP-007.01 (REQ-TRIP-002, REQ-EVID-006).

THE FIRST PRODUCT ROUTE IN THIS REPOSITORY, AND THE ONLY PUBLIC ONE

    `API-017` is declared `security: []`. That is deliberate and it is a product
    decision, not an oversight: putting coverage behind a login means asking
    somebody to register in order to be told *no*.

    Being unauthenticated has a consequence that reached back into the data model.
    A public request has no tenant, so a tenant-scoped read model is one this
    endpoint can never read — it returns an empty region list rather than an error,
    which is a well-formed and completely wrong answer about coverage. `BUG-028`,
    found by writing this handler, fixed by `016`.

WHAT THIS RESPONSE MAY NOT CONTAIN

    `REQ-EVID-006` and the contract's own description: never a provider identity,
    never a count, never a quota. Which supplier backs a region is commercially
    confidential, and how close one is to its limit tells an attacker exactly when
    the product degrades.

    So `provider_health` is one aggregate label. The projection already drops
    provider identity (`STEP-006.09`) and the table has no column for it (`015`);
    this is the third place the same rule is enforced, and the repetition is the
    point — each layer is one a future writer could reach directly.

THE CACHE IS GLOBAL BECAUSE THE DATA IS

    `REQ-SEC-001` requires a tenant on every cache key. This cache has no tenant in
    its key and that is not an exception to the rule — it is the rule applied to
    data that has no tenant. The safety property is different in kind, so it is
    tested differently: **nothing tenant-scoped may enter this cache**, asserted on
    the value rather than on the key.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol


class CoverageError(RuntimeError):
    """A coverage read was refused. No partial response was served."""


#: Coverage changes when a provider's health changes, which is minutes at worst.
#: Long enough to absorb a burst on the landing page, short enough that a
#: degradation is disclosed while it is still true (`REQ-EVID-006` names
#: cache-masking as the specific failure). Provisional pending `DEC-005`.
CACHE_TTL_SECONDS = 30.0

#: The one key. Named rather than derived so it is greppable, and so the absence
#: of a tenant in it is visible at the point somebody would add one.
COVERAGE_CACHE_KEY = "platform:coverage"

_FRESHNESS_TO_HEALTH = {"current": "healthy", "degraded": "degraded", "stale": "unavailable"}
_SEVERITY = {"healthy": 0, "degraded": 1, "unavailable": 2}


class Cursor(Protocol):
    """The slice of a DB-API cursor used here, matching `auth.db` and `domain`."""

    def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...
    def fetchall(self) -> list[tuple[Any, ...]]: ...


@dataclass
class CoverageCache:
    """A tiny time-boxed cache in front of a public, tenant-free read.

    Deliberately **not** a general-purpose cache utility. A shared one would grow a
    tenant-scoped caller, and the moment it does, this cache's global key becomes a
    cross-tenant leak rather than a correct simplification.
    """

    ttl_seconds: float = CACHE_TTL_SECONDS
    _value: dict[str, Any] | None = None
    _stored_at: float | None = None
    _keys: set[str] = field(default_factory=set)

    def cache_get(self, key: str, *, now: float) -> dict[str, Any] | None:
        if key != COVERAGE_CACHE_KEY:
            raise CoverageError(
                f"refusing cache key {key!r}. This cache holds one public document; a "
                f"second key means a caller with something else to store, and the "
                f"next one after that will have a tenant"
            )
        if self._value is None or self._stored_at is None:
            return None
        if now - self._stored_at > self.ttl_seconds:
            return None
        return self._value

    def cache_set(self, key: str, value: Mapping[str, Any], *, now: float) -> None:
        if key != COVERAGE_CACHE_KEY:
            raise CoverageError(f"refusing cache key {key!r}")
        self._value = dict(value)
        self._stored_at = now
        self._keys.add(key)

    def keys(self) -> frozenset[str]:
        """Every key this cache has held. Used by the isolation test, which asserts
        no tenant identifier has ever appeared in one."""
        return frozenset(self._keys)

    def invalidate(self) -> None:
        self._value = None
        self._stored_at = None


def _aggregate_health(regions: Sequence[Mapping[str, Any]]) -> str:
    """One label for the whole response — worst region wins.

    Never a list, never a count. A count alone reveals how many suppliers back the
    platform, which is the shape of the supply chain by another route.
    """
    if not regions:
        return "unavailable"
    worst = max(
        (_FRESHNESS_TO_HEALTH[str(r["freshness"])] for r in regions),
        key=lambda h: _SEVERITY[h],
    )
    return worst


def read_coverage(cursor: Cursor) -> dict[str, Any]:
    """Read the coverage read model. No tenant binding, because there is none.

    Deliberately does not open a `UnitOfWork`: that abstraction binds a tenant and
    refuses without one (`STEP-006.04`), which is correct for every other operation
    and wrong for this one. Using it here would mean inventing a tenant for a public
    request, and an invented tenant is a tenant somebody will later trust.
    """
    cursor.execute(
        "SELECT region_id, display_name, date_bounds_start, date_bounds_end, "
        "freshness, limitations FROM coverage_read_model ORDER BY region_id"
    )
    regions = [
        {
            "region_id": row[0],
            # Declared, not echoed from `region_id`. The first version of this
            # handler used the id as the name, which validated against nothing and
            # rendered `bern` to a traveller.
            "display_name": row[1],
            "date_bounds": {"start": row[2].isoformat(), "end": row[3].isoformat()},
            "freshness": row[4],
            "limitations": list(row[5] or []),
        }
        for row in cursor.fetchall()
    ]
    # `accepting_trips` is read by the refusal path and deliberately not selected
    # here: `CoverageRegion` is `additionalProperties: false`, and adding a field to
    # a public contract to fit an implementation is the wrong direction of fit.
    return {"regions": regions, "provider_health": _aggregate_health(regions)}


def get_coverage(
    cursor: Cursor, *, cache: CoverageCache, now: float | None = None
) -> dict[str, Any]:
    """`API-017`. Cached, public, and naming no supplier.

    The cache is checked before the read and the result is stored after it. A
    degraded region reaches the traveller within `CACHE_TTL_SECONDS`, which is the
    number `REQ-EVID-006` actually constrains — the requirement is not "do not
    cache", it is "do not present cached data as current".
    """
    moment = time.monotonic() if now is None else now
    cached = cache.cache_get(COVERAGE_CACHE_KEY, now=moment)
    if cached is not None:
        return cached
    document = read_coverage(cursor)
    cache.cache_set(COVERAGE_CACHE_KEY, document, now=moment)
    return document
