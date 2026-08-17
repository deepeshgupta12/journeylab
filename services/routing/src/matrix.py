"""Travel-time matrices and honest profile support — STEP-005.05 (REQ-A11Y-003, REQ-DATA-002).

THE PROHIBITION THIS MODULE EXISTS TO ENFORCE

    §5: "**Explicit profile-support declaration** — silent fallback from wheelchair
    to walking is prohibited."

    That is an accessibility requirement and it is also the most consequential rule
    in this step. If a provider cannot route for a wheelchair and we quietly return
    walking times, a wheelchair user receives an itinerary computed for somebody who
    can take stairs. It will look correct. Every duration will be plausible. The
    connection at Bern that requires a footbridge will be presented as a nine-minute
    transfer.

    Being told "we cannot route this reliably" is **useful**. Being given confident
    numbers computed for a different body is worse than useless, because the person
    has no way to know. `REQ-A11Y-003` requires every core action to be completable
    without the map; it does not permit substituting a different traveller's route.

    So `Profile.WHEELCHAIR` is never satisfied by walking. A provider that does not
    declare it produces `ProfileUnsupported`, which is a value the product carries
    and discloses — the same shape as `ObjectiveWithdrawn` in the weather adapter
    and `TransitUnavailable` in the transit adapter.

STRAIGHT-LINE DISTANCE IS NOT A ROUTE
    §5 again: "Straight-line distance is never substituted for a routing failure."
    Crow-flies across Lake Thun is not a walk, and across a valley it is not even a
    detour — it is a physical impossibility rendered as a duration. There is no code
    path here that produces a travel time from coordinates alone.

WHY THE CACHE KEY INCLUDES LICENCE TERMS
    A matrix derived from a source with a maximum cache duration must expire on that
    source's terms, not on ours. Keying by mode and window alone would serve a
    result past its licence-permitted retention — a contract breach that looks
    exactly like a cache hit.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class RoutingError(ValueError):
    """A routing result could not be produced honestly."""


class Profile(enum.StrEnum):
    """How a traveller moves. `WHEELCHAIR` is never a synonym for `WALKING`."""

    WALKING = "walking"
    TRANSIT = "transit"
    DRIVING = "driving"
    #: Step-free routing. Requires kerb, lift, ramp and platform data — a provider
    #: without it cannot answer, and must say so rather than approximate.
    WHEELCHAIR = "wheelchair"


@dataclass(frozen=True, slots=True)
class ProfileSupport:
    """What a provider genuinely supports, declared rather than assumed.

    `declared_by` and `evidence` are required. A provider "supporting wheelchair
    routing" is a claim, and an unattributed claim about accessibility is the thing
    this module exists to prevent — so the record says who said it and on what
    basis, and a reviewer can disagree with a named source.
    """

    provider_id: str
    profiles: frozenset[Profile]
    declared_by: str
    evidence: str

    def __post_init__(self) -> None:
        if not self.profiles:
            raise RoutingError(f"{self.provider_id}: a provider supporting nothing is not one")
        if not self.declared_by.strip() or not self.evidence.strip():
            raise RoutingError(
                f"{self.provider_id}: profile support must say who declared it and on "
                f"what basis. An unattributed accessibility claim cannot be reviewed."
            )

    def supports(self, profile: Profile) -> bool:
        return profile in self.profiles


@dataclass(frozen=True, slots=True)
class ProfileUnsupported:
    """A profile this provider cannot answer for, and what to tell the user.

    Carries **no duration field of any kind**. A nullable duration is one `or 0`
    away from becoming a travel time, and a travel time is what must not exist here.
    """

    profile: Profile
    provider_id: str
    disclosure: str

    def __post_init__(self) -> None:
        if not self.disclosure.strip():
            raise RoutingError(
                f"{self.profile}: an unsupported profile without a disclosure is the "
                f"silent substitution REQ-A11Y-003 forbids"
            )


def profile_unsupported(profile: Profile, provider_id: str) -> ProfileUnsupported:
    """Decline to answer, in words a traveller can act on."""
    disclosures = {
        Profile.WHEELCHAIR: (
            "Step-free travel times are not available for this region, so these "
            "journeys have not been checked for step-free access. They are not "
            "shown as accessible, and walking times have not been substituted."
        ),
        Profile.TRANSIT: (
            "Public transport travel times are unavailable, so these journeys were "
            "not compared using transit."
        ),
        Profile.DRIVING: "Driving times are unavailable for this region.",
        Profile.WALKING: "Walking times are unavailable for this region.",
    }
    return ProfileUnsupported(
        profile=profile, provider_id=provider_id, disclosure=disclosures[profile]
    )


@dataclass(frozen=True, slots=True)
class TravelTime:
    """One computed duration, with the provenance that makes it checkable.

    `assumptions` is a plain-language list rather than a code, because the things
    that change a duration — an assumed walking speed, whether a lift was trusted,
    whether a transfer buffer was applied — are exactly what a reviewer needs to
    read. `REQ-EVID-001` requires source and observed time on a volatile value; a
    travel time is volatile and derived, so it needs both plus the derivation.
    """

    origin_id: str
    destination_id: str
    profile: Profile
    duration: timedelta
    provider_id: str
    computed_at: datetime
    departure_at: datetime
    assumptions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("computed_at", "departure_at"):
            if getattr(self, name).tzinfo is None:
                raise RoutingError(f"{name} must be timezone-aware")
        if self.duration <= timedelta(0):
            raise RoutingError(
                f"{self.origin_id}->{self.destination_id}: duration {self.duration} is not "
                f"positive. A zero or negative travel time is a routing failure, and a "
                f"failure must surface rather than become an instant journey."
            )
        if not self.assumptions:
            raise RoutingError(
                "a travel time with no recorded assumptions cannot be reviewed "
                "(REQ-EVID-001). State the walking speed, transfer buffer or lift "
                "assumption even when it is the default."
            )


@dataclass(frozen=True, slots=True)
class MatrixKey:
    """What makes two matrix requests the same request.

    `licence_id` is part of the identity, not metadata. Two matrices for the same
    stops and window derived from differently-licensed sources have different
    retention rules, and a cache that conflates them will serve one past its terms
    (`ADR-016` §1 — the ODbL question this repository has open).
    """

    profile: Profile
    departure_window_start: datetime
    departure_window_end: datetime
    licence_id: str
    provider_id: str

    def __post_init__(self) -> None:
        if self.departure_window_end < self.departure_window_start:
            raise RoutingError("departure window ends before it starts")
        if not self.licence_id.strip():
            raise RoutingError(
                "licence_id is required in a matrix cache key: a result derived from a "
                "source with a retention limit must expire on that source's terms"
            )


def is_expired(
    key: MatrixKey, computed_at: datetime, now: datetime, max_cache_seconds: int | None
) -> bool:
    """Whether a cached matrix may still be served.

    `None` means the licence sets no limit — not "cache forever without thinking".
    The distinction is kept because the two are different facts, and a reader who
    sees `None` should understand it as "this source permits it" rather than as a
    missing value.
    """
    if now.tzinfo is None or computed_at.tzinfo is None:
        raise RoutingError("both computed_at and now must be timezone-aware")
    if max_cache_seconds is None:
        return False
    return (now - computed_at) > timedelta(seconds=max_cache_seconds)


def resolve_profile(profile: Profile, support: ProfileSupport) -> Profile | ProfileUnsupported:
    """The only way to obtain a profile for a routing request.

    Returns either the requested profile or a refusal. **There is no third
    outcome**, and in particular no downgrade: a caller that asked for a wheelchair
    profile cannot receive a walking one from this function, because the return type
    does not permit it silently — a consumer must handle `ProfileUnsupported`
    explicitly or fail to typecheck.
    """
    if support.supports(profile):
        return profile
    return profile_unsupported(profile, support.provider_id)
