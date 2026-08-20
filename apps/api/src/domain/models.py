"""Domain entities and their invariants — STEP-006.03 (REQ-DATA-007, REQ-CONS-006).

INVARIANTS LIVE IN CONSTRUCTORS, NOT IN CALLERS

    An invariant checked by the caller is an invariant checked by *some* callers.
    Every rule here is enforced where the value is built, so a second entry path —
    an admin tool, a replay, a fixture — cannot bypass it by not knowing about it.

ILLEGAL STATES ARE UNREPRESENTABLE WHERE THAT IS POSSIBLE

    `Scenario` takes its four lineage references as required arguments. There is no
    partially-constructed scenario to fix up later, because `REQ-CONS-006` says a
    run is reproducible from inputs, config, model versions and seed — and a type
    that can exist without them is a type that will.

MONEY IS AN INTEGER AND A CURRENCY, ALWAYS BOTH

    `0.1 + 0.2` is not `0.3` in IEEE 754, and currency arithmetic is mostly
    addition, so a total summed from float line items stops matching the sum of
    what is displayed. The exponent is not always two — JPY and KRW have none,
    BHD/KWD/TND have three — so only formatting divides, and adding two different
    currencies is refused rather than coerced through a rate nobody supplied.

STATE MACHINES REJECT, THEY DO NOT WARN

    `BACKEND_ARCHITECTURE` §3 distinguishes `Infeasible` from `Failed` because they
    have different recovery paths: infeasibility is a product answer with a
    conflict set, failure is an operational problem to retry. Collapsing them, or
    letting an invalid transition through with a log line, loses that distinction
    exactly when someone needs it.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from .temporal import require_aware


class DomainError(ValueError):
    """An invariant was violated. The value was NOT partially constructed."""


# --- value objects ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Money:
    """Integer minor units and an ISO 4217 code. Never floating point."""

    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount_minor, int) or isinstance(self.amount_minor, bool):
            raise DomainError(
                f"amount_minor must be an int, got {type(self.amount_minor).__name__}. "
                f"A float here is a rounding error that only appears in the total"
            )
        if len(self.currency) != 3 or not self.currency.isalpha() or not self.currency.isupper():
            raise DomainError(
                f"currency must be an ISO 4217 alphabetic code, got {self.currency!r}"
            )

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise DomainError(
                f"cannot add {self.currency} to {other.currency}. Converting would need "
                f"a rate, a rate needs a date, and neither was supplied — so the sum "
                f"would be a number nobody chose"
            )
        return Money(self.amount_minor + other.amount_minor, self.currency)

    @classmethod
    def zero(cls, currency: str) -> Self:
        return cls(0, currency)


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where a value came from. Matches `provenance.json`."""

    source_id: str
    licence_id: str
    confidence: float
    access_label: str
    observed_at: datetime

    def __post_init__(self) -> None:
        require_aware(self.observed_at, label="observed_at")
        if not 0.0 <= self.confidence <= 1.0:
            raise DomainError(f"confidence must be 0..1, got {self.confidence}")
        if self.access_label not in {"public", "display_permitted", "internal_only"}:
            raise DomainError(f"unknown access_label {self.access_label!r}")
        for label, value in (("source_id", self.source_id), ("licence_id", self.licence_id)):
            if not value.strip():
                raise DomainError(f"{label} is required — an unattributed fact cannot be cited")


@dataclass(frozen=True, slots=True)
class TemporalValidity:
    """The three axes, matching `temporal-validity.json`."""

    observed_at: datetime
    effective_from: datetime
    effective_to: datetime | None = None
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("observed_at", self.observed_at),
            ("effective_from", self.effective_from),
            ("effective_to", self.effective_to),
            ("recorded_at", self.recorded_at),
        ):
            if value is not None:
                require_aware(value, label=label)
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise DomainError("effective_to precedes effective_from — that window covers nothing")

    def covers(self, start: datetime, end: datetime) -> bool:
        """Whether the window covers the whole of [start, end).

        Whole, not partial: a window covering the first day of a three-day trip does
        not describe the other two, and letting it count silently extends a fact
        past its own validity.
        """
        require_aware(start, label="start")
        require_aware(end, label="end")
        if start < self.effective_from:
            return False
        return self.effective_to is None or end <= self.effective_to


# --- state machines -----------------------------------------------------------------


class TripState(enum.StrEnum):
    DRAFT = "draft"
    BRIEF_CONFIRMED = "brief_confirmed"
    EVIDENCE_READY = "evidence_ready"
    GENERATING = "generating"
    SCENARIOS_READY = "scenarios_ready"
    #: A product answer with a conflict set. NOT the same as FAILED.
    INFEASIBLE = "infeasible"
    #: An operational problem to retry. NOT the same as INFEASIBLE.
    FAILED = "failed"
    SELECTED = "selected"
    ACTIVATED = "activated"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    ARCHIVED = "archived"


#: `BACKEND_ARCHITECTURE` §3, as data. Written as a table rather than as `if`
#: statements so the diagram and the code can be compared by eye.
TRIP_TRANSITIONS: dict[TripState, frozenset[TripState]] = {
    TripState.DRAFT: frozenset({TripState.BRIEF_CONFIRMED, TripState.ARCHIVED}),
    TripState.BRIEF_CONFIRMED: frozenset({TripState.EVIDENCE_READY, TripState.ARCHIVED}),
    TripState.EVIDENCE_READY: frozenset({TripState.GENERATING, TripState.ARCHIVED}),
    TripState.GENERATING: frozenset(
        {TripState.SCENARIOS_READY, TripState.INFEASIBLE, TripState.FAILED}
    ),
    # Infeasible recovers by relaxing constraints — back to the brief.
    TripState.INFEASIBLE: frozenset({TripState.BRIEF_CONFIRMED, TripState.ARCHIVED}),
    # Failure recovers by retrying — back to the evidence it already had.
    TripState.FAILED: frozenset({TripState.EVIDENCE_READY, TripState.ARCHIVED}),
    TripState.SCENARIOS_READY: frozenset({TripState.SELECTED, TripState.ARCHIVED}),
    TripState.SELECTED: frozenset({TripState.ACTIVATED, TripState.ARCHIVED}),
    TripState.ACTIVATED: frozenset({TripState.REPLANNING, TripState.COMPLETED}),
    TripState.REPLANNING: frozenset({TripState.ACTIVATED}),
    TripState.COMPLETED: frozenset({TripState.ARCHIVED}),
    TripState.ARCHIVED: frozenset(),
}


def next_trip_state(current: TripState, target: TripState) -> TripState:
    """Move, or refuse. There is no third outcome.

    A rejected transition raises rather than logging and continuing: the states
    that would be conflated are `INFEASIBLE` and `FAILED`, and telling a traveller
    "no plan fits your constraints" when the truth is "a provider timed out" is a
    different product answer, not a cosmetic difference.
    """
    allowed = TRIP_TRANSITIONS[current]
    if target not in allowed:
        raise DomainError(
            f"{current} cannot become {target}. Allowed: "
            f"{sorted(s.value for s in allowed) or 'none — this is a terminal state'}"
        )
    return target


# --- entities --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScenarioLineage:
    """The four things `REQ-CONS-006` needs to reproduce a run.

    A separate type, so `Scenario` cannot be given three of them. Grouping them also
    means a new lineage input is added in one place rather than at every call site.
    """

    brief_id: str
    pack_id: str
    solver_config_hash: str
    seed: int
    model_versions: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("brief_id", self.brief_id),
            ("pack_id", self.pack_id),
            ("solver_config_hash", self.solver_config_hash),
        ):
            if not value.strip():
                raise DomainError(
                    f"{label} is required. REQ-CONS-006 makes a scenario reproducible "
                    f"from its inputs; one that cannot name them is not reproducible, "
                    f"and there is no later point at which this becomes recoverable"
                )
        if not self.model_versions:
            raise DomainError(
                "model_versions is required and may not be empty. An empty tuple "
                "records 'no models were involved', which is a claim, not a default"
            )


@dataclass(frozen=True, slots=True)
class Scenario:
    """One objective, one run, fully attributed."""

    scenario_id: str
    trip_id: str
    objective: str
    lineage: ScenarioLineage
    created_at: datetime

    def __post_init__(self) -> None:
        require_aware(self.created_at, label="created_at")
        if not self.objective.strip():
            raise DomainError("a scenario without an objective cannot be compared against another")


@dataclass(frozen=True, slots=True)
class ItineraryItem:
    """One timed element. Protection is checked here, not by the editor."""

    item_id: str
    kind: str
    starts_at: datetime
    ends_at: datetime
    time_zone: str
    cost: Money | None = None
    protected: bool = False
    completed: bool = False

    def __post_init__(self) -> None:
        require_aware(self.starts_at, label="starts_at")
        require_aware(self.ends_at, label="ends_at")
        if self.ends_at < self.starts_at:
            raise DomainError(f"{self.item_id}: an item cannot end before it starts")
        if self.kind not in {"activity", "transit", "rest", "booking", "buffer"}:
            raise DomainError(f"unknown itinerary item kind {self.kind!r}")
        if not self.time_zone.strip():
            raise DomainError(
                f"{self.item_id}: an item without a zone is wrong by an hour twice a year"
            )
        if self.completed and self.starts_at > self.ends_at:
            raise DomainError("a completed item must have a coherent window")

    def edited(self, **changes: object) -> ItineraryItem:
        """Return an edited copy, or refuse.

        `REQ-CONS-011`: an edit touching a protected item is refused until the user
        explicitly unlocks it. Enforced on the *model* rather than in the editor,
        because a replan, a repair and a bulk edit are three different callers and
        only one of them would have remembered.

        Unlocking is itself an edit, so it is the one change permitted on a
        protected item — otherwise protection could never be removed.
        """
        if self.protected and set(changes) != {"protected"}:
            raise DomainError(
                f"{self.item_id} is protected. Unlock it explicitly before editing "
                f"(REQ-CONS-011) — an automated repair must not quietly move a booked "
                f"item"
            )
        if self.completed and "completed" not in changes:
            raise DomainError(
                f"{self.item_id} is already completed; editing what has happened "
                f"rewrites the traveller's history rather than their plan"
            )
        current = {
            "item_id": self.item_id,
            "kind": self.kind,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "time_zone": self.time_zone,
            "cost": self.cost,
            "protected": self.protected,
            "completed": self.completed,
        }
        current.update(changes)
        return ItineraryItem(**current)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class TripBrief:
    """Four constraint classes in four fields, never merged.

    `constraint-class.json`: merging hard and soft "produces a solver that quietly
    relaxes a wheelchair requirement to save nine minutes"; merging `inferred` into
    either "hides that a machine put words in the traveller's mouth".
    """

    brief_id: str
    trip_id: str
    version: int
    hard: tuple[str, ...] = ()
    soft: tuple[str, ...] = ()
    inferred: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.version < 1:
            raise DomainError("brief versions start at 1")

    @property
    def is_solvable(self) -> bool:
        """`REQ-CONS-002`: an unresolved question blocks solving.

        Not a warning. A plan built on a guessed answer is confidently wrong, which
        is the failure mode this product is most concerned with.
        """
        return not self.unresolved


@dataclass
class TripAggregate:
    """A trip and its state, with transitions guarded."""

    trip_id: str
    organization_id: str
    state: TripState = TripState.DRAFT
    version: int = 1
    _history: list[tuple[TripState, TripState]] = field(default_factory=list)

    def transition_to(self, target: TripState) -> TripState:
        self.state = next_trip_state(self.state, target)
        self._history.append((self._history[-1][1] if self._history else TripState.DRAFT, target))
        self.version += 1
        return self.state

    def history(self) -> tuple[tuple[TripState, TripState], ...]:
        return tuple(self._history)
