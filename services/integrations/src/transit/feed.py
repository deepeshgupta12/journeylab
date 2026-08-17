"""Feed pinning and stop resolution — STEP-005.04 (REQ-DATA-002, TST-DATA-002).

WHY A FEED VERSION IS PINNED RATHER THAN FOLLOWED

    A GTFS feed is republished whenever the operator changes anything, and
    identifiers are **not** guaranteed stable across publications. A `stop_id` can
    be retired and later reused for a different platform; a `trip_id` can be
    renumbered wholesale.

    An evidence pack that stores `stop_id` and resolves it against whatever feed is
    current will, one day, resolve it against a different stop — and nothing about
    that failure looks like a failure. The itinerary is coherent, the citation
    resolves, and the platform is wrong.

    `REQ-CONS-006` requires a scenario to be reproducible from its inputs and
    versions. A feed version is one of those versions, so drift is a build failure
    rather than a refresh.

AN UNRESOLVABLE STOP IS A COVERAGE GAP, NOT A GUESS
    §5 states it and the reason is the same as everywhere else in this step:
    nearest-match resolution produces a plan that is confidently at the wrong
    platform. The gap is returned so it can be disclosed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


class FeedError(ValueError):
    """A feed could not be used as pinned."""


@dataclass(frozen=True, slots=True)
class FeedVersion:
    """The exact publication an evidence pack was built from.

    `content_hash` rather than the operator's own version string: a feed
    republished with the same stated version and different contents is precisely
    the case a version string cannot catch, and it is not rare.
    """

    feed_id: str
    content_hash: str
    published_at: datetime

    def __post_init__(self) -> None:
        if not self.content_hash.strip():
            raise FeedError("content_hash is required — a feed version string alone")
        if self.published_at.tzinfo is None:
            raise FeedError("published_at must be timezone-aware")


def assert_pinned(expected: FeedVersion, actual: FeedVersion) -> None:
    """Refuse to proceed against a feed that is not the pinned one.

    Raises rather than warning. A warning here would be read as "the data moved on,
    which is normal" — and the whole point is that the data moving on invalidates
    every stored identifier that references it.
    """
    if expected.feed_id != actual.feed_id:
        raise FeedError(f"expected feed {expected.feed_id!r}, got {actual.feed_id!r}")
    if expected.content_hash != actual.content_hash:
        raise FeedError(
            f"{expected.feed_id}: feed contents changed "
            f"({expected.content_hash[:12]} -> {actual.content_hash[:12]}). "
            f"Stop and trip identifiers are not stable across publications, so a "
            f"stored stop_id may now resolve to a different platform. Re-ingest and "
            f"re-pin rather than reading the new feed with old references "
            f"(REQ-CONS-006)."
        )


@dataclass(frozen=True, slots=True)
class Stop:
    stop_id: str
    name: str
    latitude: float
    longitude: float
    time_zone: str

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise FeedError(f"{self.stop_id}: latitude {self.latitude} out of range")
        if not -180.0 <= self.longitude <= 180.0:
            raise FeedError(f"{self.stop_id}: longitude {self.longitude} out of range")
        if not self.time_zone.strip():
            raise FeedError(
                f"{self.stop_id}: a stop without a zone cannot place a departure in time"
            )


@dataclass(frozen=True, slots=True)
class CoverageGap:
    """A reference we could not resolve, kept so it can be disclosed."""

    reference: str
    kind: str
    detail: str


@dataclass
class StopIndex:
    """Stop lookup that refuses to approximate."""

    stops: dict[str, Stop] = field(default_factory=dict)
    gaps: list[CoverageGap] = field(default_factory=list)

    def add(self, stop: Stop) -> None:
        self.stops[stop.stop_id] = stop

    def resolve(self, stop_id: str) -> Stop | None:
        """The stop, or None **and a recorded gap**.

        No nearest-match, no fuzzy name search. A plan built on the wrong platform
        is worse than a plan that admits it does not know the platform, and only
        the second one can be disclosed to the traveller.
        """
        stop = self.stops.get(stop_id)
        if stop is None:
            self.gaps.append(
                CoverageGap(
                    reference=stop_id,
                    kind="unresolvable_stop",
                    detail=(
                        "stop_id is not in the pinned feed. Not resolved by proximity "
                        "or name: a confidently wrong platform is worse than an "
                        "admitted gap."
                    ),
                )
            )
        return stop


# --- service alerts and their freshness ---------------------------------------

#: REQ-NFR-011: closure and disruption facts meet minute-level freshness SLOs.
#:
#: Five minutes, and the number is a PROVIDER property rather than a universal
#: truth — passed in wherever it is checked so a slower source cannot silently
#: inherit a promise this one makes.
DEFAULT_ALERT_SLO = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class ServiceAlert:
    """A disruption, with the window it applies to and when we learned of it."""

    alert_id: str
    headline: str
    effect: str
    observed_at: datetime
    active_from: datetime
    active_to: datetime | None

    def __post_init__(self) -> None:
        for name in ("observed_at", "active_from"):
            if getattr(self, name).tzinfo is None:
                raise FeedError(f"{name} must be timezone-aware")
        if self.active_to is not None and self.active_to < self.active_from:
            raise FeedError(f"{self.alert_id}: active_to precedes active_from")

    def is_stale(self, now: datetime, slo: timedelta = DEFAULT_ALERT_SLO) -> bool:
        """Whether this alert is too old to be relied on.

        Staleness is about **when we observed it**, not when it starts. A closure
        beginning tomorrow that we last confirmed a week ago is stale evidence
        about tomorrow, and `REQ-EVID-001`'s separation of observation time from
        effective time exists exactly so this can be asked.
        """
        if now.tzinfo is None:
            raise FeedError("now must be timezone-aware")
        return (now - self.observed_at) > slo

    def active_at(self, moment: datetime) -> bool:
        if moment.tzinfo is None:
            raise FeedError("moment must be timezone-aware")
        if moment < self.active_from:
            return False
        # Absent end means ongoing, not ended — the safe reading for a disruption
        # and the same rule as temporal-validity.json.
        return self.active_to is None or moment <= self.active_to


@dataclass(frozen=True, slots=True)
class TransitUnavailable:
    """No usable transit data, and what the interface must say about it.

    §5: "no transit => walking/driving only, gap disclosed". Modelled like
    `ObjectiveWithdrawn` in the weather adapter and for the same reason: the
    absence is a value the product carries, not an exception somebody catches and
    turns into silence.
    """

    reason: str
    disclosure: str
    modes_still_available: tuple[str, ...] = ("walking",)

    def __post_init__(self) -> None:
        if not self.disclosure.strip():
            raise FeedError(
                "a transit gap without a disclosure is the silent degradation REQ-DATA-003 forbids"
            )


def transit_unavailable(reason: str) -> TransitUnavailable:
    return TransitUnavailable(
        reason=reason,
        disclosure=(
            "Public transport data is unavailable for this region, so these plans "
            "use walking and driving only. Journeys that would rely on a train, "
            "bus or boat are not shown."
        ),
        modes_still_available=("walking", "driving"),
    )


def now_utc() -> datetime:
    return datetime.now(UTC)
