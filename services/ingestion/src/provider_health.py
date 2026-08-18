"""Provider health, coverage and refusal — STEP-005.10 (REQ-EVID-006, REQ-TRIP-002).

THE INTERNAL STATE MACHINE IS RICHER THAN THE EVENT VOCABULARY, ON PURPOSE

    `STEP-005.10` §5 asks for four states: healthy, degraded, circuit-open,
    recovering. `EVT-008`'s payload enum has three: healthy, degraded, unavailable,
    and the schema is closed.

    That is not a mistake in either place. The internal machine describes **our
    mechanics**; the event tells a consumer **what it can do**, and no consumer has a
    different response to "circuit open" than to "unavailable". So the mapping is
    explicit and lossy in one direction only, and `RECOVERING` maps to `degraded`
    rather than `healthy` — announcing recovery before it is proven is how a
    half-recovered provider gets traffic sent back to it.

WHY EMISSION IS ON PUBLISHED-STATE CHANGE, NOT ON EVERY INTERNAL TRANSITION

    §5 says "emitted on every transition". Taken literally against the mapping above,
    `DEGRADED -> RECOVERING` emits an event whose previous and new states are both
    `degraded` — a self-transition carrying no information a consumer can act on, and
    one the contract's own dedupe key (`provider_id + new_state`) would discard
    anyway.

    So every internal transition is **recorded** in the health history, and an event
    is emitted when the published state changes. Nothing is hidden; the stream stays
    meaningful. This is a deliberate reading of §5's intent over its wording, and it
    is recorded in `BR-049` rather than left for someone to discover as a discrepancy.

RECOVERY NEEDS HYSTERESIS OR IT IS A FLAP

    One success after an outage means the next request might work. Promoting to
    healthy on it produces oscillation: healthy, open, healthy, open — an event storm
    on the stream, and coverage that accepts and refuses trips at random, which is
    worse for a traveller than a steady refusal because it is not reproducible.

WHAT THE PUBLIC MAY LEARN, AND WHAT IT MAY NOT

    `REQ-EVID-006` requires degradation to be surfaced rather than masked by cached
    data presented as current. `Coverage` in the contract requires the opposite of
    detail: *"an aggregate. Never a list, never named, never a count — each of those
    leaks the shape of the supply chain."*

    Both hold at once because they are about different things. The traveller learns
    **that** the answer is degraded; they do not learn **who** degraded it or how
    many. `PublicCoverage` has nowhere to put a provider identity — the same
    construction as the attribution record in `.06`, where the field a leak would
    need does not exist to be filled in.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class HealthError(ValueError):
    """A health transition or coverage query was refused, and NOT guessed."""


class HealthState(enum.StrEnum):
    """Internal mechanics. Four states, mapped down to three for publication."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CIRCUIT_OPEN = "circuit_open"
    RECOVERING = "recovering"


class PublishedState(enum.StrEnum):
    """`EVT-008`'s vocabulary, and the enum in the AsyncAPI payload."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class RegionFreshness(enum.StrEnum):
    """`CoverageRegion.freshness` in the OpenAPI contract."""

    CURRENT = "current"
    DEGRADED = "degraded"
    STALE = "stale"


#: Internal state to the published vocabulary. `RECOVERING -> DEGRADED` is the load
#: bearing row: a provider that has begun answering again is not yet a provider we
#: trust, and publishing `healthy` would send full traffic to a half-recovered one.
PUBLICATION: dict[HealthState, PublishedState] = {
    HealthState.HEALTHY: PublishedState.HEALTHY,
    HealthState.DEGRADED: PublishedState.DEGRADED,
    HealthState.CIRCUIT_OPEN: PublishedState.UNAVAILABLE,
    HealthState.RECOVERING: PublishedState.DEGRADED,
}

#: Consecutive successes required before `RECOVERING` becomes `HEALTHY`. Provisional
#: pending `DEC-005`; what is not provisional is that it must exceed one. A single
#: success promotes on the first request that happens to land, which oscillates.
RECOVERY_SUCCESSES = 3


@dataclass(frozen=True, slots=True)
class HealthChanged:
    """`EVT-008` — `journey.provider.health_changed.v1`.

    `provider_id` is here and **never leaves the platform**. The AsyncAPI description
    says so explicitly, and `PublicCoverage` below is the shape that does leave.
    """

    provider_id: str
    previous_state: PublishedState
    new_state: PublishedState
    reason: str
    affected_regions: tuple[str, ...]
    at: datetime

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise HealthError(
                "EVT-008 requires a reason. A state change nobody can explain is one "
                "nobody can respond to, and the admin surface has nothing to show"
            )
        if self.previous_state is self.new_state:
            raise HealthError(
                f"{self.provider_id}: a self-transition {self.new_state} carries no "
                f"information, and the stream's dedupe key would discard it anyway"
            )

    @property
    def dedupe_key(self) -> str:
        """`x-journeylab-dedupe-key: provider_id + new_state`."""
        return f"{self.provider_id}|{self.new_state}"


@dataclass(frozen=True, slots=True)
class Transition:
    """One internal move, recorded whether or not it produced an event."""

    provider_id: str
    previous: HealthState
    new: HealthState
    reason: str
    at: datetime
    published: bool


@dataclass
class ProviderHealth:
    """One provider's health, its history, and the events it produced."""

    provider_id: str
    regions: tuple[str, ...]
    state: HealthState = HealthState.HEALTHY
    _successes: int = 0
    _history: list[Transition] = field(default_factory=list)
    _events: list[HealthChanged] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.provider_id.strip():
            raise HealthError("a provider needs an identifier")
        if not self.regions:
            raise HealthError(
                f"{self.provider_id}: a provider with no declared regions cannot have "
                f"its degradation attributed to any coverage, so the refusal path "
                f"would silently never fire"
            )

    @property
    def published(self) -> PublishedState:
        return PUBLICATION[self.state]

    def history(self) -> tuple[Transition, ...]:
        return tuple(self._history)

    def events(self) -> tuple[HealthChanged, ...]:
        return tuple(self._events)

    def _move(self, new_state: HealthState, *, reason: str, at: datetime) -> None:
        previous, previous_published = self.state, self.published
        if previous is new_state:
            return
        self.state = new_state
        publishes = previous_published is not self.published
        self._history.append(
            Transition(
                provider_id=self.provider_id,
                previous=previous,
                new=new_state,
                reason=reason,
                at=at,
                published=publishes,
            )
        )
        if publishes:
            self._events.append(
                HealthChanged(
                    provider_id=self.provider_id,
                    previous_state=previous_published,
                    new_state=self.published,
                    reason=reason,
                    affected_regions=self.regions,
                    at=at,
                )
            )

    def record_failure(self, *, reason: str, at: datetime, circuit_open: bool = False) -> None:
        """A call failed. `circuit_open` is the breaker's own verdict, not ours."""
        self._successes = 0
        self._move(
            HealthState.CIRCUIT_OPEN if circuit_open else HealthState.DEGRADED,
            reason=reason,
            at=at,
        )

    def record_success(self, *, at: datetime) -> None:
        """A call succeeded. Promotion is gated by consecutive successes.

        From `CIRCUIT_OPEN` the first success moves to `RECOVERING`, never straight
        to `HEALTHY`: one answer proves the provider replied once, and promoting on it
        oscillates between open and healthy on every other request.
        """
        if self.state is HealthState.HEALTHY:
            self._successes = RECOVERY_SUCCESSES
            return
        self._successes += 1
        if self.state is HealthState.CIRCUIT_OPEN:
            self._move(
                HealthState.RECOVERING,
                reason="a probe succeeded after the circuit opened",
                at=at,
            )
        if self._successes >= RECOVERY_SUCCESSES:
            self._move(
                HealthState.HEALTHY,
                reason=f"{self._successes} consecutive successes",
                at=at,
            )

    @property
    def successes(self) -> int:
        return self._successes


# --- coverage, and what the public is allowed to learn ---------------------------

#: Worst-first. Aggregation takes the worst state among the providers a region
#: depends on, because a region is only as available as its least available input.
_SEVERITY: dict[PublishedState, int] = {
    PublishedState.UNAVAILABLE: 2,
    PublishedState.DEGRADED: 1,
    PublishedState.HEALTHY: 0,
}


@dataclass(frozen=True, slots=True)
class PublicRegion:
    """What a client may learn about one region.

    There is deliberately **no provider field, no provider count and no list.**
    `Coverage` in the contract: *"an aggregate. Never a list, never named, never a
    count — each of those leaks the shape of the supply chain."* A count is enough to
    infer the supply chain's size, and quota proximity tells an attacker when the
    product degrades, so the shape that would carry either does not exist here.
    """

    region_id: str
    freshness: RegionFreshness
    accepting_trips: bool
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PublicCoverage:
    """The public view. One aggregate health value for the whole response."""

    regions: tuple[PublicRegion, ...]
    provider_health: PublishedState


@dataclass(frozen=True, slots=True)
class TripRefused:
    """`REQ-TRIP-002`: refused **with an explanation**, and no partial simulation.

    The explanation is a required field rather than an optional one. "We cannot plan
    this region right now" is a usable answer; a bare refusal sends the traveller to
    try again, and again.

    There is no partial result on this type and no partial result anywhere in this
    module. A half-simulated itinerary is the specific harm the requirement names,
    and it is worse than a refusal because it looks like an answer.
    """

    region_id: str
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise HealthError(
                "REQ-TRIP-002 requires an explanation. A bare refusal is indistinguishable "
                "from a bug, and the traveller retries instead of replanning"
            )


@dataclass(frozen=True, slots=True)
class TripAccepted:
    region_id: str
    #: Non-empty when the region is degraded. `REQ-EVID-006`: degradation is
    #: surfaced, never masked by cached data presented as current.
    disclosures: tuple[str, ...] = ()


@dataclass
class CoverageModel:
    """Regions, the providers they depend on, and the refusal decision.

    A region's dependencies are declared rather than inferred. A region nobody
    declared cannot be assessed, and the safe answer to "can we plan here" when we do
    not know what it needs is no.
    """

    _regions: dict[str, tuple[str, ...]] = field(default_factory=dict)
    _providers: dict[str, ProviderHealth] = field(default_factory=dict)

    def declare_region(self, region_id: str, *, depends_on: tuple[str, ...]) -> None:
        if not depends_on:
            raise HealthError(
                f"{region_id}: a region with no declared dependencies would report "
                f"healthy for ever, because there is nothing that can degrade it"
            )
        self._regions[region_id] = depends_on

    def register(self, provider: ProviderHealth) -> None:
        self._providers[provider.provider_id] = provider

    def region_state(self, region_id: str) -> PublishedState:
        """The worst state among the region's declared dependencies.

        A missing provider is `UNAVAILABLE`, not healthy. A dependency we are not
        tracking is one we know nothing about, and "no news is good news" is how an
        unmonitored provider stays green through an outage.
        """
        try:
            dependencies = self._regions[region_id]
        except KeyError as exc:
            raise HealthError(
                f"{region_id!r} is not a declared region. Answering for an undeclared "
                f"region would invent a coverage claim"
            ) from exc
        states = [
            self._providers[p].published if p in self._providers else PublishedState.UNAVAILABLE
            for p in dependencies
        ]
        return max(states, key=lambda s: _SEVERITY[s])

    def assess(self, region_id: str) -> TripAccepted | TripRefused:
        """Whether a new trip may be planned in this region.

        `REQ-TRIP-002` refuses a request "outside current coverage". An unavailable
        dependency puts the region outside coverage; a degraded one does not — it
        makes the answer less certain, which is disclosed rather than refused.
        Refusing on every degradation would refuse most of the time and teach people
        that the product is broken rather than that the data is thin.
        """
        state = self.region_state(region_id)
        if state is PublishedState.UNAVAILABLE:
            return TripRefused(
                region_id=region_id,
                reason=(
                    f"{region_id} is outside current coverage: a source this region "
                    f"depends on is unavailable. Planning it now would produce a "
                    f"partial simulation rather than a plan"
                ),
            )
        if state is PublishedState.DEGRADED:
            return TripAccepted(
                region_id=region_id,
                disclosures=(
                    f"{region_id} is running on degraded sources. Some facts may be "
                    f"older than usual and are marked where they are used.",
                ),
            )
        return TripAccepted(region_id=region_id)

    def public_view(self) -> PublicCoverage:
        """The projection a client receives. Lossy by construction.

        Every provider identity is dropped here and there is nowhere downstream to
        recover it from, which is the point: `REQ-EVID-006` is satisfied by the shape
        of the type rather than by remembering to strip a field.
        """
        regions: list[PublicRegion] = []
        for region_id in sorted(self._regions):
            state = self.region_state(region_id)
            decision = self.assess(region_id)
            regions.append(
                PublicRegion(
                    region_id=region_id,
                    freshness={
                        PublishedState.HEALTHY: RegionFreshness.CURRENT,
                        PublishedState.DEGRADED: RegionFreshness.DEGRADED,
                        PublishedState.UNAVAILABLE: RegionFreshness.STALE,
                    }[state],
                    accepting_trips=isinstance(decision, TripAccepted),
                    limitations=decision.disclosures
                    if isinstance(decision, TripAccepted)
                    else (decision.reason,),
                )
            )
        worst = (
            max(
                (r.freshness for r in regions),
                key=lambda f: {"current": 0, "degraded": 1, "stale": 2}[f],
            )
            if regions
            else RegionFreshness.CURRENT
        )
        return PublicCoverage(
            regions=tuple(regions),
            provider_health={
                RegionFreshness.CURRENT: PublishedState.HEALTHY,
                RegionFreshness.DEGRADED: PublishedState.DEGRADED,
                RegionFreshness.STALE: PublishedState.UNAVAILABLE,
            }[worst],
        )
