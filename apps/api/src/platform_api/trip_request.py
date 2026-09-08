"""Whether a planning request can be answered at all — STEP-007.03 (REQ-TRIP-002).

THE QUESTION THIS MODULE ANSWERS, AND THE ONE IT DOES NOT

    `CoverageModel.assess` (STEP-005.10) answers: *is this region plannable right
    now, given its suppliers.* That is a question about supply, and it lives in
    `services/ingestion` with the health model that can answer it.

    This module answers a different one: *is this request plannable* — a question
    about the request, which reaches the supply answer by reading the projection
    those health events produce. Pushing date bounds into `CoverageModel` would make
    the ingestion service know what a trip request is.

    Hence a second refusal type rather than an extended `TripRefused`. The new one
    carries a machine-readable `code` because STEP-007 §17 asks for "refusal rate
    **by reason**", and a sentence cannot be counted. `TripRefused` was not given
    one: adding a required field to a frozen, VERIFIED dataclass to serve a consumer
    it does not have is the wrong direction of fit.

THERE IS NO PARTIAL RESULT ON ANY PATH THROUGH HERE

    `REQ-TRIP-002` names the harm precisely: a refused request "must not produce a
    partial simulation". `PlanningRefused` has nowhere to put one — no itinerary
    field, no scenario field, no options list — and this module imports nothing that
    could build one. Both are asserted in the tests rather than left to inspection,
    because "there is no code path" is a property that stops being true silently.

TODAY IS A PROPERTY OF THE DESTINATION

    The one decision in this file that is easy to get wrong and hard to see wrong.
    A date bound is compared against "today", and today is neither the server's nor
    the browser's. See `_today_in`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from domain.temporal import TemporalError, zone_of

from platform_api.coverage import Cursor

#: Phase 1 supports 3 to 7 day trips. `PRODUCT_SCOPE` §81 and `ASM-015`: the window is
#: "large enough to demonstrate differentiated simulation without unbounded
#: complexity".
#:
#: The upper bound is `REQ-TRIP-002` applied directly — the solver is exercised at
#: 3 to 7 days, so a nine-day plan would be of unvalidated quality, and a plan of
#: unvalidated quality presented as a plan is the partial simulation the requirement
#: forbids.
#:
#: **The lower bound is declared scope that I have recommended against** (`DEC-011`,
#: `BR-061` §7). Nothing in `ASM-015`'s reasoning applies downward: a two-day trip is
#: less complex than a three-day one, not more. It is enforced as declared because
#: shipping 1-7 because I prefer it would be editing product scope through code.
#: One constant, one line to change when `DEC-011` is answered.
MIN_TRIP_DAYS = 3
MAX_TRIP_DAYS = 7


class PlanningCheckError(RuntimeError):
    """The request was malformed. Distinct from a refusal: nothing was decided."""


@dataclass(frozen=True, slots=True)
class RegionCoverage:
    """The declared facts about one region, as the read model holds them.

    A plain value rather than a row, so the rule can be tested without a database
    and so the caller cannot pass half a region.
    """

    region_id: str
    display_name: str
    date_bounds_start: date
    date_bounds_end: date
    #: IANA zone. `018` made it NOT NULL with no default, because the alternative to
    #: knowing is guessing.
    time_zone: str
    #: 'current' | 'degraded' | 'stale' — the projection's spelling of
    #: `PublishedState`. 'stale' is `UNAVAILABLE`.
    freshness: str
    accepting_trips: bool
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PlanningAccepted:
    """Planning may proceed. Carries disclosures, never a plan.

    `disclosures` is non-empty exactly when the region is degraded. `REQ-EVID-006`
    asks for degradation to be **surfaced**, and this is where it surfaces — an
    acceptance that says what is weak about it, rather than a refusal that says
    nothing.
    """

    region_id: str
    display_name: str
    nights: int
    disclosures: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PlanningRefused:
    """Planning may not proceed, and the traveller is told why.

    `code` is a registered error code, so the refusal can be counted and the
    problem document built from the register rather than composed here.

    There is deliberately no `partial`, `suggestion` or `alternatives` field. A
    refusal that carries something plan-shaped is the failure `REQ-TRIP-002` names;
    the supported bounds go in `remediation`, which is guidance, not a result.
    """

    region_id: str
    code: str
    reason: str
    #: `Problem.remediation` in the contract requires a `kind` discriminator — "an
    #: error must tell the user what to do next". Enforced below rather than left to
    #: the schema test, which only sees the refusals a test happens to construct.
    remediation: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if self.remediation is not None and not str(self.remediation.get("kind", "")).strip():
            raise PlanningCheckError(
                "remediation requires a `kind`. The contract makes it the one fixed "
                "field: a structured next step the client can branch on, rather than "
                "prose it has to parse"
            )
        if not self.reason.strip():
            raise PlanningCheckError(
                "REQ-TRIP-002 requires an explanation. A bare refusal is "
                "indistinguishable from a bug, and the traveller retries instead of "
                "replanning"
            )


PlanningDecision = PlanningAccepted | PlanningRefused


def read_region(cursor: Cursor, region_id: str) -> RegionCoverage | None:
    """One region, shaped for the rule. `None` when nothing is declared under that id.

    A second reader over `coverage_read_model`, deliberately. `read_coverage` builds
    the public document and omits `accepting_trips` and `time_zone` because the
    contract forbids the first and does not need the second; this one needs both and
    does not need to be safe to publish. Two projections of one table, each shaped
    for its consumer, rather than one shape that is wrong for both.

    Like `read_coverage`, it opens no `UnitOfWork`: coverage is global (`BUG-028`,
    `016`) and there is no tenant to bind. An invented tenant is a tenant somebody
    later trusts.
    """
    cursor.execute(
        "SELECT region_id, display_name, date_bounds_start, date_bounds_end, "
        "time_zone, freshness, accepting_trips, limitations "
        "FROM coverage_read_model WHERE region_id = %s",
        (region_id,),
    )
    rows = cursor.fetchall()
    if not rows:
        return None
    row = rows[0]
    return RegionCoverage(
        region_id=row[0],
        display_name=row[1],
        date_bounds_start=row[2],
        date_bounds_end=row[3],
        time_zone=row[4],
        freshness=row[5],
        accepting_trips=row[6],
        limitations=tuple(row[7] or ()),
    )


def _today_in(zone_name: str, *, now: datetime) -> date:
    """The current calendar date **at the destination**.

    Not the server's date and not the browser's. At 23:30 UTC on 4 September it is
    already the 5th in Zurich and still the 4th in Honolulu; a traveller in Honolulu
    asking about 5 September in Bern is asking about tomorrow-there, which is
    today-here. Whichever clock is picked as the default, one of those two people is
    told their date is in the past when it is not — and it renders as an off-by-one
    in a date picker, which is why it gets reported as a display bug.

    `now` is a required argument with no default. A function that reaches for the
    wall clock itself cannot be tested across a boundary it is supposed to handle,
    and the boundary is the whole point of this function.
    """
    return now.astimezone(zone_of(zone_name)).date()


def check_planning_request(
    *,
    region: RegionCoverage | None,
    region_id: str,
    start: date,
    end: date,
    now: datetime,
) -> PlanningDecision:
    """Decide whether a planning request can be answered. Deterministic.

    `region` is `None` when nothing is declared under `region_id`. That is passed in
    rather than looked up here so the rule needs no database and the caller keeps its
    own transaction — the same reason `domain.temporal` returns SQL fragments instead
    of executing them.

    The order of the checks is not arbitrary. Identity first, then the shape of the
    request, then the request against the region's declared window, then supply.
    Answering "your dates are outside our window" for a region that does not exist
    would leak the shape of a region that is not there; answering "the provider is
    down" for a malformed date would send the traveller to wait for a recovery that
    would not help them.
    """
    if region is None:
        return PlanningRefused(
            region_id=region_id,
            code="coverage.unsupported_region",
            reason=(
                f"We do not cover {region_id!r} yet. It is not one of the regions "
                f"JourneyLab has declared support for, so we cannot plan there — "
                f"and planning it anyway would produce a guess, not a plan."
            ),
            remediation={"kind": "choose_supported_region"},
        )

    if end < start:
        raise PlanningCheckError(
            "end is before start. This is a malformed request rather than an "
            "unsupported one: there is nothing to refuse, because no trip was "
            "described"
        )

    # Inclusive of both endpoints — 1st to 3rd is three days away, two nights. The
    # traveller counts days; the solver will count nights. Both are stated because
    # this is where the off-by-one would live.
    days = (end - start).days + 1
    nights = days - 1

    if days < MIN_TRIP_DAYS or days > MAX_TRIP_DAYS:
        return PlanningRefused(
            region_id=region.region_id,
            code="coverage.unsupported_dates",
            reason=(
                f"JourneyLab plans trips of {MIN_TRIP_DAYS} to {MAX_TRIP_DAYS} days. "
                f"Those dates are {days} days. We would rather say so than produce a "
                f"plan we have not validated at that length."
            ),
            remediation={
                "kind": "adjust_trip_length",
                "supported_trip_days": {"minimum": MIN_TRIP_DAYS, "maximum": MAX_TRIP_DAYS},
                "requested_days": days,
            },
        )

    try:
        today = _today_in(region.time_zone, now=now)
    except TemporalError as exc:
        # A region whose declared zone is not a real zone cannot have its dates
        # checked at all. Refusing is the only honest answer: falling back to UTC
        # would answer the question with a clock nobody chose, which is the entire
        # failure `018` exists to prevent.
        raise PlanningCheckError(
            f"{region.region_id} declares a time zone that is not a known IANA zone. "
            f"Its dates cannot be validated and no fallback zone is substituted"
        ) from exc

    if start < today:
        return PlanningRefused(
            region_id=region.region_id,
            code="coverage.unsupported_dates",
            reason=(
                f"That start date has already passed in {region.display_name}, where "
                f"it is {today.isoformat()}. Dates are checked in the destination's "
                f"time zone, not yours, so this can differ by a day from your calendar."
            ),
            remediation={
                "kind": "choose_future_dates",
                "today_at_destination": today.isoformat(),
            },
        )

    if start < region.date_bounds_start or end > region.date_bounds_end:
        return PlanningRefused(
            region_id=region.region_id,
            code="coverage.unsupported_dates",
            reason=(
                f"We can plan {region.display_name} between "
                f"{region.date_bounds_start.isoformat()} and "
                f"{region.date_bounds_end.isoformat()}. Those dates fall outside that "
                f"window, and we do not have the data to plan them."
            ),
            remediation={
                "kind": "choose_supported_dates",
                "supported_dates": {
                    "start": region.date_bounds_start.isoformat(),
                    "end": region.date_bounds_end.isoformat(),
                },
            },
        )

    # --- supply -------------------------------------------------------------------
    #
    # THE TWO SENSES OF "DEGRADED", AND WHY THIS IS NOT ONE BRANCH
    #   `ERROR_MODEL.md` names `coverage.provider_degraded` "provider health
    #   INSUFFICIENT FOR RELIABLE PLANNING" — which is `PublishedState.UNAVAILABLE`,
    #   projected here as 'stale'. It is not the published state spelled `degraded`,
    #   which STEP-005.10 defines as *less certain, and disclosed*.
    #
    #   Collapsing them would be a serious regression rather than a simplification:
    #   `PUBLICATION[RECOVERING] is DEGRADED`, so a provider that has just come back
    #   publishes `degraded` for its whole recovery window. Refusing on that state
    #   would turn every recovery — including from a blip — into a total outage, and
    #   the hysteresis added to protect the provider would start refusing travellers.
    #   `BUG-034`, `BR-061` §3.
    if region.freshness == "stale" or not region.accepting_trips:
        return PlanningRefused(
            region_id=region.region_id,
            code="coverage.provider_degraded",
            reason=(
                f"We cannot plan {region.display_name} right now. A source this region "
                f"depends on is unavailable, and planning without it would produce a "
                f"partial simulation rather than a plan. This is usually temporary."
            ),
        )

    disclosures: tuple[str, ...] = ()
    if region.freshness == "degraded":
        disclosures = (
            f"{region.display_name} is running on degraded sources. Some facts may be "
            f"older than usual and are marked where they are used.",
        )

    return PlanningAccepted(
        region_id=region.region_id,
        display_name=region.display_name,
        nights=nights,
        # Declared limitations are shown alongside any degradation disclosure, not
        # instead of it. They answer different questions: one is what this region is
        # always like, the other is what is wrong with it today.
        disclosures=disclosures + tuple(region.limitations),
    )
