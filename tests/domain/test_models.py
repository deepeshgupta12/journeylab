"""Domain invariants — TST-DATA-007 · STEP-006.03.

WHAT THESE ARE PROTECTING
    Rules that are true only where they are enforced. Every one of these can be
    bypassed by a second entry path — an admin tool, a replay, a fixture — unless
    the constructor refuses:

      money as float        -> a total that stops matching the sum of what is shown
      partial lineage       -> a scenario nobody can reproduce (REQ-CONS-006)
      merged constraints    -> a solver that relaxes a wheelchair requirement
      protected item edited -> an automated repair moves a booked flight
      infeasible == failed  -> "no plan fits" told to someone whose provider timed out
"""

from __future__ import annotations

from dataclasses import fields as dataclass_fields
from datetime import UTC, datetime, timedelta

import pytest
from domain.models import (
    TRIP_TRANSITIONS,
    DomainError,
    ItineraryItem,
    Money,
    Provenance,
    Scenario,
    ScenarioLineage,
    TemporalValidity,
    TripAggregate,
    TripBrief,
    TripState,
    next_trip_state,
)
from domain.temporal import TemporalError

NOW = datetime(2026, 8, 20, 9, 0, tzinfo=UTC)


def lineage(**overrides: object) -> ScenarioLineage:
    base: dict[str, object] = {
        "brief_id": "brief-1",
        "pack_id": "pack-1",
        "solver_config_hash": "cfg-1",
        "seed": 42,
        "model_versions": (("solver", "1.0"),),
    }
    base.update(overrides)
    return ScenarioLineage(**base)  # type: ignore[arg-type]


def item(**overrides: object) -> ItineraryItem:
    base: dict[str, object] = {
        "item_id": "item-1",
        "kind": "activity",
        "starts_at": NOW,
        "ends_at": NOW + timedelta(hours=2),
        "time_zone": "Europe/Zurich",
    }
    base.update(overrides)
    return ItineraryItem(**base)  # type: ignore[arg-type]


# --- money -------------------------------------------------------------------------


class TestMoneyIsNeverFloatingPoint:
    def test_a_float_amount_is_refused(self) -> None:
        """`0.1 + 0.2` is not `0.3`, and currency arithmetic is mostly addition — so
        a total summed from floats stops matching the sum of what is displayed."""
        with pytest.raises(DomainError, match="must be an int"):
            Money(12.34, "CHF")  # type: ignore[arg-type]

    def test_a_bool_is_not_an_int_here(self) -> None:
        """`True` is an `int` in Python. Accepting it would let a flag become a
        price, which is the kind of thing that survives review.

        No `type: ignore` below, and its absence is the point: `bool` is a subtype
        of `int`, so mypy is perfectly happy with this call. The static checker
        cannot catch it, which is why the runtime guard exists.
        """
        with pytest.raises(DomainError, match="must be an int"):
            Money(True, "CHF")

    def test_adding_two_currencies_is_refused_rather_than_converted(self) -> None:
        """Converting needs a rate, a rate needs a date, and neither was supplied —
        so the sum would be a number nobody chose."""
        with pytest.raises(DomainError, match="cannot add CHF to EUR"):
            Money(100, "CHF") + Money(100, "EUR")

    def test_zero_decimal_currencies_are_representable(self) -> None:
        """The exponent is not always 2: JPY and KRW have none. Only formatting
        divides, so the model does not assume hundredths."""
        assert (Money(100, "JPY") + Money(23, "JPY")).amount_minor == 123

    @pytest.mark.parametrize("bad", ["chf", "CHFX", "CH", "12F", ""])
    def test_a_non_iso_currency_is_refused(self, bad: str) -> None:
        with pytest.raises(DomainError, match="ISO 4217"):
            Money(1, bad)


# --- lineage -----------------------------------------------------------------------


class TestAScenarioCannotExistWithoutItsLineage:
    @pytest.mark.parametrize("missing", ["brief_id", "pack_id", "solver_config_hash"])
    def test_each_reference_is_required(self, missing: str) -> None:
        """REQ-CONS-006 is enforced by the type rather than by a later check, because
        there is no later point at which an unreproducible run becomes recoverable."""
        with pytest.raises(DomainError, match="is required"):
            lineage(**{missing: "  "})

    def test_empty_model_versions_is_refused(self) -> None:
        """An empty tuple records "no models were involved", which is a claim rather
        than a default — so it has to be stated, not omitted."""
        with pytest.raises(DomainError, match="may not be empty"):
            lineage(model_versions=())

    def test_a_seed_of_zero_is_valid(self) -> None:
        """Zero is a seed. Treating falsy as missing would silently reject it and the
        run would look unreproducible for a reason nobody could see."""
        assert lineage(seed=0).seed == 0

    def test_lineage_is_a_required_argument_of_scenario(self) -> None:
        """No partially-constructed scenario to fix up later."""
        with pytest.raises(TypeError):
            Scenario(scenario_id="s", trip_id="t", objective="fastest", created_at=NOW)  # type: ignore[call-arg]

    def test_a_scenario_needs_an_objective_to_be_compared(self) -> None:
        with pytest.raises(DomainError, match="objective"):
            Scenario(scenario_id="s", trip_id="t", objective=" ", lineage=lineage(), created_at=NOW)


# --- state machine -------------------------------------------------------------------


class TestTripTransitions:
    def test_infeasible_and_failed_recover_differently(self) -> None:
        """The distinction `BACKEND_ARCHITECTURE` §3 draws, asserted.

        Infeasible is a product answer — relax the constraints, so back to the
        brief. Failed is operational — retry, so back to the evidence already
        gathered. Collapsing them tells a traveller "no plan fits your constraints"
        when a provider timed out.
        """
        assert TripState.BRIEF_CONFIRMED in TRIP_TRANSITIONS[TripState.INFEASIBLE]
        assert TripState.EVIDENCE_READY in TRIP_TRANSITIONS[TripState.FAILED]
        assert TripState.EVIDENCE_READY not in TRIP_TRANSITIONS[TripState.INFEASIBLE]
        assert TripState.BRIEF_CONFIRMED not in TRIP_TRANSITIONS[TripState.FAILED]

    def test_an_invalid_transition_raises_rather_than_warning(self) -> None:
        with pytest.raises(DomainError, match="cannot become"):
            next_trip_state(TripState.GENERATING, TripState.SELECTED)

    def test_archived_is_terminal_and_says_so(self) -> None:
        with pytest.raises(DomainError, match="terminal state"):
            next_trip_state(TripState.ARCHIVED, TripState.DRAFT)

    def test_every_state_has_an_entry_in_the_table(self) -> None:
        """A state added to the enum without a row would raise `KeyError` at the
        moment it was first reached, which is production."""
        assert set(TRIP_TRANSITIONS) == set(TripState)

    def test_every_state_except_archived_can_reach_archived(self) -> None:
        """`REQ-PRIV-006` deletion runs from archived. A state that cannot get there
        is a trip that can never be deleted."""
        for state in TripState:
            if state is TripState.ARCHIVED:
                continue
            reachable: set[TripState] = {state}
            frontier: list[TripState] = [state]
            while frontier:
                for nxt in TRIP_TRANSITIONS[frontier.pop()]:
                    if nxt not in reachable:
                        reachable.add(nxt)
                        frontier.append(nxt)
            assert TripState.ARCHIVED in reachable, state

    def test_the_aggregate_records_what_it_did(self) -> None:
        trip = TripAggregate(trip_id="t", organization_id="o")
        trip.transition_to(TripState.BRIEF_CONFIRMED)
        trip.transition_to(TripState.EVIDENCE_READY)
        assert trip.state is TripState.EVIDENCE_READY
        assert trip.version == 3
        assert len(trip.history()) == 2


# --- protection -------------------------------------------------------------------------


class TestProtectedAndCompletedItems:
    def test_a_protected_item_refuses_an_edit(self) -> None:
        """REQ-CONS-011, enforced on the model. A replan, a repair and a bulk edit
        are three callers, and only one of them would have remembered."""
        with pytest.raises(DomainError, match="is protected"):
            item(protected=True).edited(starts_at=NOW + timedelta(hours=1))

    def test_unlocking_is_the_one_edit_a_protected_item_accepts(self) -> None:
        """Otherwise protection could never be removed, and REQ-CONS-011 says
        "until the user explicitly unlocks it"."""
        unlocked = item(protected=True).edited(protected=False)
        assert unlocked.protected is False

    def test_a_completed_item_cannot_be_rewritten(self) -> None:
        """Editing what has happened rewrites the traveller's history rather than
        their plan."""
        with pytest.raises(DomainError, match="already completed"):
            item(completed=True).edited(starts_at=NOW)

    def test_an_ordinary_item_edits_normally(self) -> None:
        moved = item().edited(starts_at=NOW + timedelta(hours=1))
        assert moved.starts_at == NOW + timedelta(hours=1)
        assert moved.item_id == "item-1"

    def test_an_item_cannot_end_before_it_starts(self) -> None:
        with pytest.raises(DomainError, match="cannot end before"):
            item(ends_at=NOW - timedelta(hours=1))

    def test_an_unknown_kind_is_refused(self) -> None:
        with pytest.raises(DomainError, match="unknown itinerary item kind"):
            item(kind="teleport")


# --- brief ---------------------------------------------------------------------------------


class TestTheFourConstraintClassesStaySeparate:
    def test_the_brief_has_four_distinct_fields(self) -> None:
        """`constraint-class.json`: merging hard and soft produces a solver that
        quietly relaxes a wheelchair requirement to save nine minutes."""
        names = {f.name for f in dataclass_fields(TripBrief)}
        assert {"hard", "soft", "inferred", "unresolved"} <= names

    def test_an_unresolved_question_blocks_solving(self) -> None:
        """REQ-CONS-002. Not a warning — a plan built on a guessed answer is
        confidently wrong."""
        assert TripBrief("b", "t", 1, unresolved=("which airport?",)).is_solvable is False
        assert TripBrief("b", "t", 1, hard=("step-free",)).is_solvable is True

    def test_versions_start_at_one(self) -> None:
        with pytest.raises(DomainError, match="start at 1"):
            TripBrief("b", "t", 0)


# --- value objects ---------------------------------------------------------------------------


class TestTemporalAndProvenanceValueObjects:
    def test_partial_cover_is_not_cover(self) -> None:
        """A window covering the first day of a three-day trip does not describe the
        other two."""
        window = TemporalValidity(
            observed_at=NOW, effective_from=NOW, effective_to=NOW + timedelta(days=1)
        )
        assert window.covers(NOW, NOW + timedelta(days=1)) is True
        assert window.covers(NOW, NOW + timedelta(days=3)) is False

    def test_an_open_ended_window_covers_anything_after_it_starts(self) -> None:
        window = TemporalValidity(observed_at=NOW, effective_from=NOW)
        assert window.covers(NOW, NOW + timedelta(days=3650)) is True

    def test_a_backwards_window_is_refused(self) -> None:
        with pytest.raises(DomainError, match="covers nothing"):
            TemporalValidity(
                observed_at=NOW, effective_from=NOW, effective_to=NOW - timedelta(days=1)
            )

    def test_naive_timestamps_are_refused(self) -> None:
        with pytest.raises(TemporalError, match="naive"):
            TemporalValidity(
                observed_at=datetime(2026, 8, 20, 9, 0),  # noqa: DTZ001
                effective_from=NOW,
            )

    def test_provenance_requires_attribution(self) -> None:
        with pytest.raises(DomainError, match="unattributed fact cannot be cited"):
            Provenance(
                source_id=" ",
                licence_id="ODbL-1.0",
                confidence=0.9,
                access_label="public",
                observed_at=NOW,
            )

    @pytest.mark.parametrize("bad", [-0.1, 1.1, 2.0])
    def test_confidence_outside_zero_to_one_is_refused(self, bad: float) -> None:
        """A confidence of 1.4 is not "very confident" — it is a scale error, and it
        propagates into ranking as a weight nobody chose. The places adapter has the
        same guard and its own test; a second class needs its own, because a shared
        rule is not shared coverage.
        """
        with pytest.raises(DomainError, match=r"confidence must be 0\.\.1"):
            Provenance(
                source_id="osm",
                licence_id="ODbL-1.0",
                confidence=bad,
                access_label="public",
                observed_at=NOW,
            )

    def test_an_unknown_access_label_is_refused(self) -> None:
        with pytest.raises(DomainError, match="access_label"):
            Provenance(
                source_id="osm",
                licence_id="ODbL-1.0",
                confidence=0.9,
                access_label="probably_fine",
                observed_at=NOW,
            )
