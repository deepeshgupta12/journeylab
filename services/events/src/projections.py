"""Read-model projection and rebuild — STEP-006.09 (REQ-DATA-010).

REPLAY AND REBUILD ARE OPPOSITES, AND THAT IS THE WHOLE MODULE

    STEP-006.07 spent its effort making sure a replayed event does **not** re-apply
    its effect. This sub-step needs the exact reverse: a rebuild re-applies every
    event, from the beginning, into an empty projection.

    Run a rebuild through an idempotent consumer and it produces a half-empty read
    model — every event already in the processed log is skipped, so the projection
    is rebuilt from whatever happened to be left. The rebuild *succeeds*. Nothing
    errors. The output is simply wrong in a way that looks like missing data.

    So `rebuild` resets the target first and does not consult the processed log at
    all. The two paths share an event stream and share nothing else, and the reason
    they must not share a mechanism is that their correctness conditions are
    contradictory.

A PROJECTION THAT READS ANYTHING BUT THE EVENT IS NOT REBUILDABLE

    A handler that queries current state — "what is this provider's health now" —
    produces today's answer while folding a year-old event. The rebuild finishes,
    the numbers differ from the original, and nothing points at the cause.

    `REQ-DATA-010` claims read models rebuild from the log. That claim holds only if
    the fold is a pure function of the events, so `Projection.apply` receives the
    envelope and the accumulated state and has no other input. A test asserts the
    module reaches no clock and no database.

FINISHING IS NOT MATCHING

    A rebuild that completes proves the code ran. `verify_rebuild` compares the
    rebuilt state against the live one and reports the differences, because the
    failure this whole design protects against — a projection that silently drifted
    from its log — is invisible to a rebuild that only checks for exceptions.
"""

from __future__ import annotations

import ast
import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from consumers import in_key_order
from outbox import Envelope


class ProjectionError(RuntimeError):
    """A projection or rebuild rule was violated. No state was partially written."""


#: A fold step: previous state and one event, returning the next state. Pure by
#: contract — see the module docstring. Anything it reads other than its arguments
#: makes the projection unrebuildable while still appearing to work.
Fold = Callable[[Mapping[str, Any], Envelope], Mapping[str, Any]]


@dataclass
class Projection:
    """One derived view, folded from the event log."""

    name: str
    fold: Fold
    #: Which event types this projection consumes. Declared rather than inferred so
    #: a projection that silently stops matching an event type is a visible change
    #: rather than a quietly emptier read model.
    handles: frozenset[str]
    state: dict[str, Any] = field(default_factory=dict)
    last_event_id: str | None = None
    last_occurred_at: datetime | None = None
    rebuilt_at: datetime | None = None

    def apply(self, envelope: Envelope) -> bool:
        """Fold one event in. Returns whether it was consumed."""
        if envelope.event_type not in self.handles:
            return False
        self.state = dict(self.fold(self.state, envelope))
        self.last_event_id = envelope.event_id
        self.last_occurred_at = envelope.occurred_at
        return True

    def consume(self, envelopes: Sequence[Envelope]) -> int:
        """Fold a batch in per-key order."""
        return sum(1 for envelope in in_key_order(envelopes) if self.apply(envelope))


def rebuild(projection: Projection, log: Sequence[Envelope], *, at: datetime) -> int:
    """Reconstruct the projection from the log. Resets first, deliberately.

    The reset is what makes this a rebuild rather than a replay. Folding into
    existing state would double every counter and leave stale keys that no event
    removes — a projection that is *more* wrong after being repaired.

    Idempotent by construction: running it twice from the same log gives the same
    state, because the second run starts from empty again. Resumability is a
    property of the *log*, not of a cursor here — the log is the position.
    """
    if at.tzinfo is None:
        raise ProjectionError("a rebuild timestamp must be timezone-aware")
    projection.state = {}
    projection.last_event_id = None
    projection.last_occurred_at = None
    folded = projection.consume(log)
    projection.rebuilt_at = at
    return folded


@dataclass(frozen=True, slots=True)
class RebuildVerification:
    """What a rebuild proved, or failed to.

    `matches` is not `completed`. A rebuild that ran without raising says the code
    works; it says nothing about whether the live projection had drifted, which is
    the failure `REQ-DATA-010` exists to make survivable.
    """

    projection: str
    matches: bool
    only_in_live: tuple[str, ...]
    only_in_rebuilt: tuple[str, ...]
    differing: tuple[str, ...]

    @property
    def detail(self) -> str:
        if self.matches:
            return f"{self.projection}: rebuilt state matches live"
        return (
            f"{self.projection}: {len(self.only_in_live)} key(s) only live, "
            f"{len(self.only_in_rebuilt)} only rebuilt, {len(self.differing)} differing"
        )


def verify_rebuild(
    live: Mapping[str, Any], rebuilt: Mapping[str, Any], *, name: str
) -> RebuildVerification:
    """Compare a rebuilt projection against the live one, key by key."""
    only_live = tuple(sorted(set(live) - set(rebuilt)))
    only_rebuilt = tuple(sorted(set(rebuilt) - set(live)))
    differing = tuple(sorted(k for k in set(live) & set(rebuilt) if live[k] != rebuilt[k]))
    return RebuildVerification(
        projection=name,
        matches=not (only_live or only_rebuilt or differing),
        only_in_live=only_live,
        only_in_rebuilt=only_rebuilt,
        differing=differing,
    )


def projection_lag(projection: Projection, *, now: datetime) -> timedelta:
    """How far behind the projection is, measured from the fact.

    Not from `rebuilt_at`. A projection that stopped folding an hour ago has a
    recent rebuild timestamp and an hour of unapplied events — the same trap as
    relay lag in `.06` and freshness in `BUG-026`, for the third time in this step.
    """
    if projection.last_occurred_at is None:
        return timedelta(0)
    return now - projection.last_occurred_at


def reads_only_its_arguments(module: Any) -> bool:
    """Whether a projection module reaches outside its inputs.

    An AST walk rather than a text scan — a substring search cannot tell code from
    prose *about* code, which is how the same check failed against its own docstring
    in `STEP-006.05`.
    """
    tree = ast.parse(inspect.getsource(module))
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    return called.isdisjoint(
        {"now", "utcnow", "today", "execute", "fetchone", "fetchall", "getenv"}
    )


# --- the first projection ------------------------------------------------------------

COVERAGE_EVENTS = frozenset({"journey.provider.health_changed.v1"})

#: `EVT-008`'s published states to `CoverageRegion.freshness`. Kept as data next to
#: the fold so the mapping is reviewable without reading the function.
_FRESHNESS_BY_STATE = {"healthy": "current", "degraded": "degraded", "unavailable": "stale"}


#: Worst first. A region is only as available as its least available provider.
_SEVERITY = {"current": 0, "degraded": 1, "stale": 2}


def fold_coverage(state: Mapping[str, Any], envelope: Envelope) -> Mapping[str, Any]:
    """Fold provider health into the coverage read model.

    A REGION IS THE WORST OF ITS PROVIDERS' **CURRENT** STATES — BUG-037
        The rule was always "a region is only as available as its least available
        input, so a healthy provider must not overwrite a degraded sibling's verdict".
        The first version enforced it by taking `max(existing, new)` severity per
        region and dropping `provider_id` on the way in. With no memory of *which*
        provider degraded a region, "worst of the providers' current states"
        collapsed into **"worst state ever observed"**: a provider coming back could
        not be told apart from a healthy sibling, so it was always worsened back, and
        a region that lost a provider once was refused for ever — live, and after a
        rebuild, which replays the same fold over the same log.

        So each region row carries `providers`: every provider's latest state for that
        region. The region's freshness is derived from that map on every event, which
        is what lets it improve. `EVT-008` declares its state **absolute, not
        incremental** (`x-journeylab-replay`), and this is that reading: each event
        replaces one provider's state rather than adding to a count.

    WHERE PROVIDER IDENTITY MAY BE, AND WHERE IT MAY NOT
        `REQ-EVID-006` and the AsyncAPI description: `provider_id` "never leaves the
        platform", and the public document carries one aggregate. The rule enforced
        here is therefore **never persisted and never published**, not "never held in
        memory" — a fold that cannot remember a provider cannot let that provider
        recover. `read_models.apply_coverage_state` writes only the three derived
        columns and `coverage_read_model` has no column to put a provider in; both are
        asserted, on the SQL parameters and on the public document.

    WHICH REGIONS AN EVENT TOUCHES
        When `affected_regions` is present it is the provider's **complete** region
        set: the new state applies to those regions, and the provider is released from
        any other region it was recorded against. Otherwise a provider that stopped
        serving a region would keep degrading it for ever — BUG-037 again, reached
        through a configuration change rather than an outage.

        `affected_regions` is optional in the contract. When it is absent, the new
        state applies to every region where the provider is already known, so a
        recovery that names no regions still clears what its outage degraded.

    An unknown `new_state` folds as `stale`: an event nobody can read must not
    produce an acceptance.
    """
    new_state: dict[str, Any] = {region: dict(row) for region, row in state.items()}
    provider = str(envelope.payload_ids.get("provider_id", "")).strip()
    freshness = _FRESHNESS_BY_STATE.get(str(envelope.payload_ids.get("new_state", "")), "stale")
    listed = [
        region.strip()
        for region in str(envelope.payload_ids.get("affected_regions", "")).split(",")
        if region.strip()
    ]
    known = [region for region, row in new_state.items() if provider in row.get("providers", {})]

    if listed:
        applies_to = listed
        # The event names this provider's complete region set. A region it no longer
        # lists no longer depends on it, so its last verdict must not keep that region
        # degraded — BUG-037's failure, reached through a configuration change.
        released = [region for region in known if region not in listed]
    else:
        applies_to = known
        released = []

    for region_id in dict.fromkeys(applies_to):
        providers = dict(new_state.get(region_id, {}).get("providers", {}))
        providers[provider] = freshness
        new_state[region_id] = _region_row(region_id, providers)
    for region_id in released:
        providers = dict(new_state[region_id]["providers"])
        providers.pop(provider, None)
        new_state[region_id] = _region_row(region_id, providers)
    return new_state


def _region_row(region_id: str, providers: Mapping[str, str]) -> dict[str, Any]:
    """A region's derived row from its providers' current states.

    Worst wins. A region with no provider currently affecting it is `current` — the
    same default the fold has always used for a region it has heard nothing bad about.
    """
    worst = max(providers.values(), key=_SEVERITY.__getitem__, default="current")
    return {
        "freshness": worst,
        "accepting_trips": worst != "stale",
        "limitations": []
        if worst == "current"
        else [f"{region_id} is running on degraded sources"],
        "providers": dict(providers),
    }


def coverage_projection() -> Projection:
    return Projection(name="coverage", fold=fold_coverage, handles=COVERAGE_EVENTS)
