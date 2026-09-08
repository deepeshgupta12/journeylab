"""STEP-007.03 — date and geography validation (REQ-TRIP-001, REQ-TRIP-002).

WHAT THESE TESTS ARE FOR, BEYOND THE RULES THEMSELVES

    Two properties here cannot be observed behaviourally yet and are asserted
    structurally instead — the practice established at STEP-005.03:

      * "no partial simulation" — there is no scenario engine to fail to produce
        one, so the assertion is on the refusal type having nowhere to put a plan
        and the module importing nothing that could build one.
      * "dates are evaluated in the destination's zone" — a rule that returned the
        right answer for the server's zone would pass every same-zone test, so the
        zone tests are written across the date line, where the two answers differ.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
from dataclasses import fields
from datetime import UTC, date, datetime, timedelta

import pytest
from platform_api import trip_request
from platform_api.trip_request import (
    MAX_TRIP_DAYS,
    MIN_TRIP_DAYS,
    PlanningAccepted,
    PlanningCheckError,
    PlanningRefused,
    RegionCoverage,
    check_planning_request,
    read_region,
)

#: Deliberately the Swiss zone: `DEC-002` chose Switzerland, and Europe/Zurich has a
#: DST transition, so the same fixture serves both the zone tests and the DST one.
ZONE = "Europe/Zurich"


def region(**overrides: object) -> RegionCoverage:
    base = {
        "region_id": "ch-bernese-oberland",
        "display_name": "Bernese Oberland",
        "date_bounds_start": date(2026, 1, 1),
        "date_bounds_end": date(2026, 12, 31),
        "time_zone": ZONE,
        "freshness": "current",
        "accepting_trips": True,
        "limitations": (),
    }
    base.update(overrides)
    return RegionCoverage(**base)  # type: ignore[arg-type]


def check(**overrides: object):  # type: ignore[no-untyped-def]
    args = {
        "region": region(),
        "region_id": "ch-bernese-oberland",
        "start": date(2026, 6, 1),
        "end": date(2026, 6, 4),
        "now": datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
    }
    args.update(overrides)
    return check_planning_request(**args)  # type: ignore[arg-type]


class TestGeography:
    def test_an_undeclared_region_is_refused_and_named(self) -> None:
        decision = check(region=None, region_id="fr-corsica")
        assert isinstance(decision, PlanningRefused)
        assert decision.code == "coverage.unsupported_region"
        assert "fr-corsica" in decision.reason

    def test_a_declared_region_within_bounds_is_accepted(self) -> None:
        assert isinstance(check(), PlanningAccepted)

    def test_an_unknown_region_is_answered_before_its_dates_are_examined(self) -> None:
        """Order matters, and not only for tidiness.

        Answering "your dates are outside our window" for a region that does not
        exist would describe the bounds of a region that is not there.
        """
        decision = check(
            region=None, region_id="fr-corsica", start=date(1990, 1, 1), end=date(1990, 1, 4)
        )
        assert isinstance(decision, PlanningRefused)
        assert decision.code == "coverage.unsupported_region"


class TestDatesAreReadInTheDestinationsZone:
    """The bug this sub-step was written to prevent.

    Every test here is constructed so that the destination's calendar date and the
    server's differ. A rule that used `datetime.now(UTC).date()` — or the caller's
    zone — passes a same-zone test perfectly and fails all of these.
    """

    def test_a_date_already_past_at_the_destination_is_refused(self) -> None:
        # 22:30 UTC on 1 June is 00:30 on 2 June in Zurich. A request for 1 June is
        # for a day that has ended there, while UTC still calls it today.
        decision = check(
            start=date(2026, 6, 1),
            end=date(2026, 6, 4),
            now=datetime(2026, 6, 1, 22, 30, tzinfo=UTC),
        )
        assert isinstance(decision, PlanningRefused)
        assert decision.code == "coverage.unsupported_dates"
        assert decision.remediation == {
            "kind": "choose_future_dates",
            "today_at_destination": "2026-06-02",
        }

    def test_the_same_instant_in_utc_would_have_accepted_it(self) -> None:
        """The negative control for the test above.

        Without it, the refusal proves only that some check fired — not that the
        destination's zone is what produced it. Here the identical instant, with the
        region declared in UTC, accepts. The zone is the only difference.
        """
        decision = check(
            region=region(time_zone="UTC"),
            start=date(2026, 6, 1),
            end=date(2026, 6, 4),
            now=datetime(2026, 6, 1, 22, 30, tzinfo=UTC),
        )
        assert isinstance(decision, PlanningAccepted)

    def test_a_traveller_east_of_the_destination_is_not_told_their_date_has_passed(self) -> None:
        """The Honolulu case from `BR-061` §5, in the direction that is easy to miss.

        13:30 in Honolulu on 4 September is 23:30 UTC, which is already 5 September
        in Zurich. Asking about 5 September in Bern is asking about tomorrow-there —
        and it must not be refused as past merely because Zurich has ticked over.
        """
        decision = check(
            start=date(2026, 9, 5),
            end=date(2026, 9, 8),
            now=datetime(2026, 9, 4, 23, 30, tzinfo=UTC),
        )
        assert isinstance(decision, PlanningAccepted)

    def test_today_at_the_destination_is_accepted_not_refused(self) -> None:
        """The boundary itself. `start < today` refuses; `start == today` must not."""
        decision = check(
            start=date(2026, 6, 2),
            end=date(2026, 6, 5),
            now=datetime(2026, 6, 1, 22, 30, tzinfo=UTC),  # 2 June in Zurich
        )
        assert isinstance(decision, PlanningAccepted)

    def test_a_trip_spanning_a_dst_transition_counts_calendar_days_not_hours(self) -> None:
        """25 October 2026 is 25 hours long in Zurich.

        The trip is four calendar days and must be counted as four. A rule that
        subtracted instants would make this trip a different length from the same
        four dates in July, and the length is what the 3 to 7 day bound is applied to.
        """
        decision = check(start=date(2026, 10, 24), end=date(2026, 10, 27))
        assert isinstance(decision, PlanningAccepted)
        assert decision.nights == 3

    def test_a_region_whose_zone_is_not_a_real_zone_is_refused_not_defaulted(self) -> None:
        """No fallback to UTC. Guessing the zone is the failure `018` exists to stop."""
        with pytest.raises(PlanningCheckError, match="not a known IANA zone"):
            check(region=region(time_zone="Europe/Atlantis"))


class TestDeclaredWindow:
    def test_a_start_before_the_window_is_refused_with_the_bounds(self) -> None:
        decision = check(
            region=region(date_bounds_start=date(2026, 7, 1)),
            start=date(2026, 6, 1),
            end=date(2026, 6, 4),
        )
        assert isinstance(decision, PlanningRefused)
        assert decision.remediation == {
            "kind": "choose_supported_dates",
            "supported_dates": {"start": "2026-07-01", "end": "2026-12-31"},
        }

    def test_an_end_after_the_window_is_refused(self) -> None:
        decision = check(
            region=region(date_bounds_end=date(2026, 6, 2)),
            start=date(2026, 6, 1),
            end=date(2026, 6, 4),
        )
        assert isinstance(decision, PlanningRefused)
        assert decision.code == "coverage.unsupported_dates"

    def test_the_window_is_inclusive_at_both_ends(self) -> None:
        decision = check(
            region=region(date_bounds_start=date(2026, 6, 1), date_bounds_end=date(2026, 6, 4)),
            start=date(2026, 6, 1),
            end=date(2026, 6, 4),
        )
        assert isinstance(decision, PlanningAccepted)


class TestTripLength:
    @pytest.mark.parametrize("days", [MIN_TRIP_DAYS, 5, MAX_TRIP_DAYS])
    def test_a_supported_length_is_accepted(self, days: int) -> None:
        decision = check(start=date(2026, 6, 1), end=date(2026, 6, 1) + timedelta(days=days - 1))
        assert isinstance(decision, PlanningAccepted)
        assert decision.nights == days - 1

    @pytest.mark.parametrize("days", [1, MIN_TRIP_DAYS - 1, MAX_TRIP_DAYS + 1, 30])
    def test_an_unsupported_length_is_refused_with_the_range(self, days: int) -> None:
        decision = check(start=date(2026, 6, 1), end=date(2026, 6, 1) + timedelta(days=days - 1))
        assert isinstance(decision, PlanningRefused)
        assert decision.code == "coverage.unsupported_dates"
        assert decision.remediation is not None
        assert decision.remediation["supported_trip_days"] == {
            "minimum": MIN_TRIP_DAYS,
            "maximum": MAX_TRIP_DAYS,
        }
        assert decision.remediation["requested_days"] == days

    def test_days_are_inclusive_of_both_endpoints(self) -> None:
        """1st to 3rd is three days and two nights.

        Asserted directly because every length bound depends on it, and an
        off-by-one here would shift the whole supported range by a day while every
        other test still passed.
        """
        decision = check(start=date(2026, 6, 1), end=date(2026, 6, 3))
        assert isinstance(decision, PlanningAccepted)
        assert decision.nights == 2

    def test_the_declared_bounds_match_product_scope(self) -> None:
        """`PRODUCT_SCOPE` §81 says 3 to 7 days. `DEC-011` may widen the lower bound.

        This test exists so that widening it is a deliberate edit with a decision
        attached, rather than a constant somebody adjusts to make a test pass.
        """
        assert (MIN_TRIP_DAYS, MAX_TRIP_DAYS) == (3, 7)


class TestMalformedRequestsAreNotRefusals:
    def test_end_before_start_raises_rather_than_refusing(self) -> None:
        """Nothing was decided, so there is nothing to refuse.

        Answering "we do not cover those dates" would be a false statement about
        coverage for a request that never described a trip.
        """
        with pytest.raises(PlanningCheckError, match="end is before start"):
            check(start=date(2026, 6, 4), end=date(2026, 6, 1))


class TestSupply:
    def test_a_stale_region_is_refused(self) -> None:
        decision = check(region=region(freshness="stale", accepting_trips=False))
        assert isinstance(decision, PlanningRefused)
        assert decision.code == "coverage.provider_degraded"

    def test_a_region_not_accepting_trips_is_refused_even_when_fresh(self) -> None:
        """`accepting_trips` is the flag `STEP-007` §23 suspends a region with.

        It must refuse on its own — a region suspended by an operator while its data
        is still current is exactly the case a freshness-only check would miss.
        """
        decision = check(region=region(freshness="current", accepting_trips=False))
        assert isinstance(decision, PlanningRefused)
        assert decision.code == "coverage.provider_degraded"

    def test_a_degraded_region_is_accepted_with_a_disclosure(self) -> None:
        """BUG-034. `REQ-EVID-006` asks for degradation to be **surfaced**.

        Refusing here would make every provider recovery a total outage, because
        `PUBLICATION[RECOVERING] is DEGRADED` — a provider that has just come back
        publishes `degraded` for its whole recovery window.
        """
        decision = check(region=region(freshness="degraded"))
        assert isinstance(decision, PlanningAccepted)
        assert decision.disclosures
        assert "degraded" in decision.disclosures[0]

    def test_the_disclosure_says_what_is_wrong_not_merely_that_something_is(self) -> None:
        """A non-empty tuple was the weak assertion `STEP-005.10` caught in itself."""
        decision = check(region=region(freshness="degraded"))
        assert isinstance(decision, PlanningAccepted)
        assert "older than usual" in decision.disclosures[0]

    def test_a_healthy_region_discloses_nothing(self) -> None:
        decision = check()
        assert isinstance(decision, PlanningAccepted)
        assert decision.disclosures == ()

    def test_limitations_are_carried_alongside_a_degradation_disclosure(self) -> None:
        """They answer different questions and neither replaces the other."""
        decision = check(region=region(freshness="degraded", limitations=("Ferries are seasonal",)))
        assert isinstance(decision, PlanningAccepted)
        assert len(decision.disclosures) == 2
        assert "Ferries are seasonal" in decision.disclosures


class TestNoPartialSimulation:
    """`REQ-TRIP-002`, asserted structurally.

    There is no scenario engine yet, so no test can watch a scenario fail to be
    produced. These assert the two properties that make it impossible: the type has
    nowhere to put a plan, and the module cannot build one. When `STEP-011` lands
    this should be upgraded to a behavioural assertion.
    """

    def test_the_refusal_type_has_no_field_a_plan_could_occupy(self) -> None:
        names = {f.name for f in fields(PlanningRefused)}
        assert names == {"region_id", "code", "reason", "remediation"}

    def test_the_acceptance_type_has_no_field_a_plan_could_occupy(self) -> None:
        names = {f.name for f in fields(PlanningAccepted)}
        assert names == {"region_id", "display_name", "nights", "disclosures"}

    def test_the_module_imports_nothing_that_could_produce_an_itinerary(self) -> None:
        source = pathlib.Path(inspect.getfile(trip_request)).read_text()
        imported: set[str] = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        forbidden = {"scenario", "itinerary", "solver", "routing", "optimis", "optimiz"}
        offenders = {m for m in imported if any(word in m.lower() for word in forbidden)}
        assert not offenders, f"a validation module reached for a planner: {offenders}"

    def test_a_refusal_carries_no_alternative_trip(self) -> None:
        """`remediation` is guidance, not a result.

        The distinction is thin enough to erode: a `remediation` that grew a
        `suggested_dates` field would be a plan by another name. Bounds are facts
        about coverage; dates chosen for the traveller would not be.
        """
        decision = check(start=date(2026, 6, 1), end=date(2026, 7, 30))
        assert isinstance(decision, PlanningRefused)
        assert decision.remediation is not None
        assert set(decision.remediation) <= {
            "kind",
            "supported_trip_days",
            "requested_days",
            "supported_dates",
            "today_at_destination",
        }


class TestRemediationIsActionable:
    """`Problem.remediation` requires `kind` — "an error must tell the user what to
    do next". A refusal whose remediation lacked it validated as a Problem nowhere
    and was found by the contract test, not by reading the code."""

    def test_a_remediation_without_a_kind_is_refused_at_the_type(self) -> None:
        with pytest.raises(PlanningCheckError, match="requires a `kind`"):
            PlanningRefused(
                region_id="ch-x",
                code="coverage.unsupported_dates",
                reason="because",
                remediation={"supported_dates": {"start": "2026-01-01", "end": "2026-12-31"}},
            )

    def test_every_refusal_the_rule_emits_carries_a_kind(self) -> None:
        """Enumerated rather than spot-checked: a refusal added later without a kind
        would otherwise only fail if somebody remembered to test it."""
        decisions = [
            check(region=None, region_id="nowhere"),
            check(start=date(2026, 6, 1), end=date(2026, 7, 30)),
            check(
                start=date(2026, 6, 1),
                end=date(2026, 6, 4),
                now=datetime(2026, 6, 1, 22, 30, tzinfo=UTC),
            ),
            check(
                region=region(date_bounds_start=date(2026, 7, 1)),
                start=date(2026, 6, 1),
                end=date(2026, 6, 4),
            ),
        ]
        for decision in decisions:
            assert isinstance(decision, PlanningRefused), decision
            assert decision.remediation is not None, decision.code
            assert decision.remediation["kind"], decision.code


class TestRefusalsExplainThemselves:
    def test_a_refusal_without_a_reason_is_refused_at_the_type(self) -> None:
        with pytest.raises(PlanningCheckError, match="requires an explanation"):
            PlanningRefused(region_id="ch-x", code="coverage.unsupported_region", reason="  ")

    def test_every_refusal_code_is_in_the_register(self) -> None:
        """A code the register does not know cannot become a problem document.

        `problem()` would raise at the moment of refusing — turning an honest "no"
        into a 500, at exactly the point the product is meant to be trustworthy.
        """
        from conventions.error_codes import ERROR_CODES

        scenarios = [
            check(region=None, region_id="unknown"),
            check(start=date(2026, 6, 1), end=date(2026, 7, 30)),
            check(region=region(freshness="stale", accepting_trips=False)),
        ]
        for decision in scenarios:
            assert isinstance(decision, PlanningRefused)
            assert decision.code in ERROR_CODES
            assert ERROR_CODES[decision.code].status is not None


class TestReadRegion:
    """`read_region` against a stub cursor. The database-backed path is in
    `test_app.py`, where a real row exercises the column list."""

    class _Cursor:
        def __init__(self, *rows: tuple[object, ...]) -> None:
            self._rows = list(rows)
            self.query = ""
            self.params: tuple[object, ...] = ()

        def execute(self, query: str, params: tuple[object, ...] = (), /) -> None:
            self.query, self.params = query, params

        def fetchall(self) -> list[tuple[object, ...]]:
            return self._rows

    def test_an_undeclared_region_reads_as_none_not_as_an_error(self) -> None:
        assert read_region(self._Cursor(), "nowhere") is None

    def test_a_row_becomes_the_value_the_rule_consumes(self) -> None:
        cursor = self._Cursor(
            (
                "ch-bo",
                "Bernese Oberland",
                date(2026, 1, 1),
                date(2026, 12, 31),
                ZONE,
                "current",
                True,
                ["Ferries are seasonal"],
            )
        )
        got = read_region(cursor, "ch-bo")
        assert got == RegionCoverage(
            region_id="ch-bo",
            display_name="Bernese Oberland",
            date_bounds_start=date(2026, 1, 1),
            date_bounds_end=date(2026, 12, 31),
            time_zone=ZONE,
            freshness="current",
            accepting_trips=True,
            limitations=("Ferries are seasonal",),
        )

    def test_the_read_binds_no_tenant(self) -> None:
        """Coverage is global (`BUG-028`, `016`). An invented tenant is one somebody
        later trusts, and a tenant-scoped read here returns an empty, well-formed and
        completely wrong answer about coverage."""
        cursor = self._Cursor()
        read_region(cursor, "ch-bo")
        assert "organization_id" not in cursor.query
        assert cursor.params == ("ch-bo",)

    def test_the_read_selects_the_columns_the_rule_needs(self) -> None:
        """`read_coverage` deliberately omits `accepting_trips` and `time_zone`.

        This one needs both, and a silent drift back to the public projection's
        column list would make every region look healthy and UTC.
        """
        cursor = self._Cursor()
        read_region(cursor, "ch-bo")
        for column in ("time_zone", "accepting_trips", "date_bounds_start", "date_bounds_end"):
            assert column in cursor.query
