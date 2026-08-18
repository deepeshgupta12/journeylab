"""Field-specific freshness and applicability — STEP-005.08 (REQ-DATA-005, REQ-EVID-005).

AGE IS MEASURED FROM WHEN THE SOURCE SAW IT, NEVER FROM WHEN WE FETCHED IT

    This is the whole module in one sentence, and getting it wrong is invisible.

    Fetch a value at 09:00 that the provider last refreshed three days ago, and
    measured from ingestion it is zero seconds old. Every dashboard reports fresh
    data. The provider's own cache — the thing most likely to be stale, and the
    thing we cannot see — becomes structurally invisible to us, and the staler the
    upstream gets the *fresher* our numbers look, because a re-fetch resets the
    clock we chose to read.

    So `TemporalFact` carries both times, `assess` uses `observed_at`, and a mutant
    that swaps them is killed by a test. Both are carried deliberately: if only
    `observed_at` existed the mistake would be unrepresentable, but so would the
    proof that we avoided it, and the gap between the two is itself a signal — a
    large one means the provider is serving us its own cache.

FRESHNESS AND APPLICABILITY ARE DIFFERENT AXES

    A fact observed sixty seconds ago about last summer's ferry timetable is
    perfectly fresh and completely inapplicable. A fact observed in March, effective
    until October, is four months old in July and exactly right.

    Conflating the two produces confident wrong answers in both directions: discard
    good seasonal data because it is old, or serve expired data because it was read
    recently. `TemporalValidity` in the contract exists for this reason and this
    module checks both axes separately, names which one failed, and checks
    applicability first — a fresh fact about the wrong window will not be fixed by
    re-fetching, so reporting "stale" would send someone to do useless work.

STALENESS IS COMPUTED AT USE AND NEVER STORED

    There is no `is_stale` field anywhere here, because a stored boolean is wrong as
    soon as the clock moves and nothing tells you when it became wrong. `assess`
    takes `now` as an argument. A test asserts the module exposes no stored flag.

WHAT THIS MODULE DELIBERATELY DOES NOT DO

    It does not compute a confidence penalty. `REQ-EVID-005` requires stale facts to
    lower scenario confidence *or* block the option; blocking is decided here because
    it follows from the field class, but the confidence *curve* is the scenario
    scorer's, and inventing a multiplier here would put a magic number in the wrong
    module — the exact shape of `BUG-026`. `staleness_ratio` is published instead:
    how far past its own threshold the fact is, as a number the scorer can use and a
    reviewer can argue with.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class FreshnessError(ValueError):
    """A freshness input was refused, and NOT assessed with a guessed value."""


class FieldClass(enum.StrEnum):
    """What kind of fact this is. There is no default and no catch-all.

    An unregistered field class raises rather than falling back, because a lenient
    default is how a closure quietly inherits a description's ninety-day threshold.
    """

    DISRUPTION = "disruption"
    HOURS = "hours"
    PRICE = "price"
    DESCRIPTION = "description"


class Severity(enum.StrEnum):
    """What staleness costs. `REQ-EVID-005` allows either, per field."""

    #: Stale means the option is blocked. Used where staleness can produce a
    #: hard-constraint violation, which `BUG_REGISTER` defines as S1.
    BLOCKING = "blocking"
    #: Stale means the fact is marked and confidence falls. Used where staleness
    #: makes an answer *less certain* rather than *wrong*.
    ADVISORY = "advisory"


class Verdict(enum.StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    #: Past threshold on a blocking field.
    EXPIRED = "expired"
    #: The fact's effective window does not cover the dates it is being used for.
    #: A coverage gap, not a staleness problem, and re-fetching will not fix it.
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class FreshnessPolicy:
    """One field class's threshold, with the reason it has that value.

    The rationale is a required field. A threshold without one is a number nobody
    can review, and `BUG-026` is what that costs: a constant justified by a belief
    about the world rather than by anything checkable.
    """

    field_class: FieldClass
    max_age: timedelta
    severity: Severity
    rationale: str

    def __post_init__(self) -> None:
        if self.max_age <= timedelta(0):
            raise FreshnessError(f"{self.field_class}: max_age must be positive")
        if not self.rationale.strip():
            raise FreshnessError(
                f"{self.field_class}: a threshold without a rationale cannot be reviewed"
            )


#: The registry. **These values are provisional pending `DEC-005`** (KPI thresholds
#: undefined) and are marked as such rather than presented as settled.
#:
#: What is *not* provisional is their ordering. `REQ-DATA-005` requires that "hours
#: and disruptions must expire faster than descriptive content", which is a property
#: of the table rather than of any one number — so it is asserted as an invariant
#: and survives whatever `DEC-005` decides the absolute values should be.
POLICIES: dict[FieldClass, FreshnessPolicy] = {
    FieldClass.DISRUPTION: FreshnessPolicy(
        field_class=FieldClass.DISRUPTION,
        max_age=timedelta(minutes=5),
        severity=Severity.BLOCKING,
        rationale=(
            "A disruption that began six minutes ago must already be visible, and one "
            "that cleared six minutes ago must stop blocking a plan. This is the only "
            "class where the traveller is standing on a platform while the fact ages."
        ),
    ),
    FieldClass.HOURS: FreshnessPolicy(
        field_class=FieldClass.HOURS,
        max_age=timedelta(hours=6),
        severity=Severity.BLOCKING,
        rationale=(
            "Same-day changes — a public holiday, an unplanned closure — have to be "
            "caught before someone is standing outside a locked door. Blocking rather "
            "than advisory because hours read wrong is a hard-constraint violation "
            "(REQ-CONS-004), which this repository defines as S1."
        ),
    ),
    FieldClass.PRICE: FreshnessPolicy(
        field_class=FieldClass.PRICE,
        max_age=timedelta(days=7),
        severity=Severity.ADVISORY,
        rationale=(
            "A week-old price makes a budget estimate less certain; it does not make "
            "the plan impossible. Advisory rather than blocking because refusing every "
            "option with a week-old price would refuse nearly everything, and "
            "REQ-EVID-003 already governs showing an estimate as an estimate."
        ),
    ),
    FieldClass.DESCRIPTION: FreshnessPolicy(
        field_class=FieldClass.DESCRIPTION,
        max_age=timedelta(days=90),
        severity=Severity.ADVISORY,
        rationale=(
            "Descriptive content ages slowly and its staleness is cosmetic. Named "
            "explicitly so the contrast with hours and disruptions is a value in a "
            "table rather than an assumption in someone's head."
        ),
    ),
}


def policy_for(field_class: FieldClass) -> FreshnessPolicy:
    """The policy for a field class, or a refusal.

    No default. A field class with no policy is a gap in the registry, and answering
    it with a lenient fallback is how a blocking field silently becomes advisory.
    """
    try:
        return POLICIES[field_class]
    except KeyError as exc:
        raise FreshnessError(
            f"no freshness policy for {field_class!r}. Add one to POLICIES with a "
            f"rationale — there is deliberately no default, because a default is how "
            f"a critical field inherits a description's threshold"
        ) from exc


@dataclass(frozen=True, slots=True)
class TemporalFact:
    """A fact and its three time axes, matching `temporal-validity.json`.

    `recorded_at` is carried and never used for age. It is here so the ingestion lag
    — `recorded_at - observed_at` — is visible, and so a test can prove which of the
    two the assessment actually reads.
    """

    field_class: FieldClass
    #: When the SOURCE stated it. The only axis age is measured from.
    observed_at: datetime
    #: When the fact starts being true in the world.
    effective_from: datetime
    #: `None` means open-ended. Per the contract: absent is **not** expired.
    effective_to: datetime | None = None
    #: When we wrote it down. Our lag, not the source's.
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("observed_at", self.observed_at),
            ("effective_from", self.effective_from),
            ("effective_to", self.effective_to),
            ("recorded_at", self.recorded_at),
        ):
            if value is not None and value.tzinfo is None:
                raise FreshnessError(f"{label} must be timezone-aware")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise FreshnessError(
                f"effective_to {self.effective_to.isoformat()} precedes effective_from "
                f"{self.effective_from.isoformat()} — a window that ends before it "
                f"starts covers nothing and would silently fail every check"
            )

    def ingestion_lag(self, *, unknown: timedelta | None = None) -> timedelta | None:
        """How long we took to record what the source already knew.

        Ours to fix, and not evidence about the fact. Published because a lag that
        grows is the visible symptom of an ingestion problem nothing else reports.
        """
        if self.recorded_at is None:
            return unknown
        return self.recorded_at - self.observed_at


@dataclass(frozen=True, slots=True)
class UseWindow:
    """The dates a fact is being used for — normally the trip's."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise FreshnessError("a use window must be timezone-aware at both ends")
        if self.end < self.start:
            raise FreshnessError("a use window cannot end before it starts")


@dataclass(frozen=True, slots=True)
class Assessment:
    """The verdict, and everything needed to argue with it."""

    verdict: Verdict
    field_class: FieldClass
    age: timedelta
    max_age: timedelta
    severity: Severity
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise FreshnessError("an assessment states why; a bare verdict cannot be reviewed")

    @property
    def blocks_option(self) -> bool:
        """Whether the option resting on this fact must be blocked.

        `REQ-EVID-005`: block, or lower confidence. Blocking applies to a blocking
        field that is either past its threshold or about the wrong dates — in both
        cases the plan would rest on something we do not actually know.
        """
        return self.severity is Severity.BLOCKING and self.verdict in {
            Verdict.EXPIRED,
            Verdict.NOT_APPLICABLE,
        }

    @property
    def staleness_ratio(self) -> float:
        """Age as a multiple of the threshold. 1.0 is exactly at the limit.

        Published instead of a confidence multiplier. How confidence should fall with
        staleness is the scenario scorer's curve to own; a number invented here would
        be a magic constant in the wrong module.
        """
        return self.age / self.max_age


def assess(fact: TemporalFact, *, now: datetime, used_for: UseWindow) -> Assessment:
    """Classify a fact for use at `now`, over `used_for`.

    Applicability is checked **before** freshness. A fresh fact about the wrong
    window is not fixed by re-fetching, so reporting it as stale would send someone
    to do work that cannot help.
    """
    if now.tzinfo is None:
        raise FreshnessError("now must be timezone-aware")
    policy = policy_for(fact.field_class)
    age = now - fact.observed_at

    if age < timedelta(0):
        # Provider clock skew. Treating a future observation as maximally fresh
        # would make it fresh forever, which is the same both-edges argument the
        # webhook replay window makes in STEP-005.06.
        raise FreshnessError(
            f"{fact.field_class}: observed_at is {(-age)} in the future. A fact from "
            f"the future is a clock problem, and accepting it would make it fresh "
            f"permanently"
        )

    def result(verdict: Verdict, reason: str) -> Assessment:
        return Assessment(
            verdict=verdict,
            field_class=fact.field_class,
            age=age,
            max_age=policy.max_age,
            severity=policy.severity,
            reason=reason,
        )

    if used_for.start < fact.effective_from:
        return result(
            Verdict.NOT_APPLICABLE,
            f"the fact takes effect {fact.effective_from.isoformat()}, after the use "
            f"window opens {used_for.start.isoformat()} — re-fetching will not fix this",
        )
    if fact.effective_to is not None and used_for.end > fact.effective_to:
        return result(
            Verdict.NOT_APPLICABLE,
            f"the fact stops being true {fact.effective_to.isoformat()}, before the use "
            f"window closes {used_for.end.isoformat()}. Partial cover is a coverage "
            f"gap, not a fact about the uncovered days",
        )

    if age <= policy.max_age:
        return result(Verdict.FRESH, f"observed {age} ago, within {policy.max_age}")

    if policy.severity is Severity.BLOCKING:
        return result(
            Verdict.EXPIRED,
            f"observed {age} ago against a {policy.max_age} threshold. {policy.rationale}",
        )
    return result(
        Verdict.STALE,
        f"observed {age} ago against a {policy.max_age} threshold — marked, and "
        f"confidence lowered by the consumer",
    )
