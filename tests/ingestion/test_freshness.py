"""Field-specific freshness — TST-DATA-005, TST-EVID-005 · STEP-005.08.

WHAT THESE ARE PROTECTING
    Two failures, and both produce a confident wrong itinerary rather than an error:

      age measured from ingestion  -> a provider serving three-day-old cache reads
                                      as perfectly fresh, and gets fresher the more
                                      often we poll it
      freshness conflated with
      applicability                -> a fact observed a minute ago about last
                                      summer's timetable passes every check
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta

import pytest
from freshness import (
    POLICIES,
    Assessment,
    FieldClass,
    FreshnessError,
    FreshnessPolicy,
    Severity,
    TemporalFact,
    UseWindow,
    Verdict,
    assess,
    policy_for,
)

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
TRIP = UseWindow(start=NOW, end=NOW + timedelta(days=3))


def fact(
    field_class: FieldClass,
    *,
    observed_ago: timedelta,
    effective_from: datetime | None = None,
    effective_to: datetime | None = None,
    recorded_ago: timedelta | None = None,
) -> TemporalFact:
    return TemporalFact(
        field_class=field_class,
        observed_at=NOW - observed_ago,
        effective_from=effective_from or (NOW - timedelta(days=365)),
        effective_to=effective_to,
        recorded_at=None if recorded_ago is None else NOW - recorded_ago,
    )


# --- the central rule -----------------------------------------------------------


class TestAgeIsMeasuredFromObservation:
    def test_a_freshly_fetched_stale_value_is_stale(self) -> None:
        """The failure this module exists to prevent.

        The provider last refreshed these hours three days ago and served them to us
        one second ago. Measured from ingestion the fact is a second old and every
        dashboard is green. Measured from observation it is three days past a
        six-hour threshold.
        """
        stale = fact(
            FieldClass.HOURS, observed_ago=timedelta(days=3), recorded_ago=timedelta(seconds=1)
        )
        result = assess(stale, now=NOW, used_for=TRIP)
        assert result.verdict is Verdict.EXPIRED
        assert result.blocks_option

    def test_ingestion_lag_is_visible_rather_than_used(self) -> None:
        """Both times are carried on purpose. With only `observed_at` the mistake
        would be unrepresentable — and so would the proof that we avoided it."""
        lagged = fact(
            FieldClass.HOURS, observed_ago=timedelta(hours=5), recorded_ago=timedelta(hours=1)
        )
        assert lagged.ingestion_lag() == timedelta(hours=4)
        assert assess(lagged, now=NOW, used_for=TRIP).verdict is Verdict.FRESH

    def test_a_fact_from_the_future_is_refused(self) -> None:
        """Provider clock skew. Accepting it would make the fact fresh permanently —
        the same both-edges argument the webhook replay window makes in `.06`."""
        with pytest.raises(FreshnessError, match="in the future"):
            assess(fact(FieldClass.HOURS, observed_ago=-timedelta(hours=1)), now=NOW, used_for=TRIP)


# --- the second axis ------------------------------------------------------------


class TestApplicabilityIsNotFreshness:
    def test_a_fact_observed_seconds_ago_about_last_summer_does_not_apply(self) -> None:
        expired_season = fact(
            FieldClass.HOURS,
            observed_ago=timedelta(seconds=30),
            effective_from=NOW - timedelta(days=400),
            effective_to=NOW - timedelta(days=300),
        )
        result = assess(expired_season, now=NOW, used_for=TRIP)
        assert result.verdict is Verdict.NOT_APPLICABLE
        assert result.blocks_option

    def test_a_four_month_old_seasonal_fact_that_covers_the_trip_is_usable(self) -> None:
        """The other direction, and the one a single timestamp gets wrong. A ferry
        timetable observed in March and effective to October is not stale in July."""
        seasonal = fact(
            FieldClass.DESCRIPTION,
            observed_ago=timedelta(days=30),
            effective_from=NOW - timedelta(days=120),
            effective_to=NOW + timedelta(days=60),
        )
        assert assess(seasonal, now=NOW, used_for=TRIP).verdict is Verdict.FRESH

    def test_partial_cover_is_a_gap_rather_than_a_fact_about_the_rest(self) -> None:
        """The window covers the first day of a three-day trip. The remaining two
        days are not described by this fact and must not inherit it."""
        partial = fact(
            FieldClass.HOURS,
            observed_ago=timedelta(hours=1),
            effective_to=NOW + timedelta(days=1),
        )
        result = assess(partial, now=NOW, used_for=TRIP)
        assert result.verdict is Verdict.NOT_APPLICABLE
        assert "Partial cover" in result.reason

    def test_an_open_ended_window_is_not_an_expired_one(self) -> None:
        """`temporal-validity.json`: "Absent is not the same as expired, and a
        consumer must not treat it as such"."""
        open_ended = fact(FieldClass.HOURS, observed_ago=timedelta(hours=1), effective_to=None)
        assert assess(open_ended, now=NOW, used_for=TRIP).verdict is Verdict.FRESH

    def test_applicability_is_reported_before_staleness(self) -> None:
        """Both are wrong; the verdict names the one that matters. Re-fetching fixes
        staleness and cannot fix a fact about the wrong dates, so reporting "stale"
        would send someone to do work that cannot help."""
        both = fact(
            FieldClass.HOURS,
            observed_ago=timedelta(days=30),
            effective_from=NOW - timedelta(days=400),
            effective_to=NOW - timedelta(days=300),
        )
        assert assess(both, now=NOW, used_for=TRIP).verdict is Verdict.NOT_APPLICABLE


# --- the registry ---------------------------------------------------------------


class TestFieldClassesExpireIndependently:
    @pytest.mark.parametrize("field_class", list(FieldClass))
    def test_every_field_class_has_a_policy_with_a_rationale(self, field_class: FieldClass) -> None:
        policy = policy_for(field_class)
        assert policy.max_age > timedelta(0)
        assert len(policy.rationale) > 40, "a threshold nobody can review is a number"

    def test_hours_and_disruptions_expire_faster_than_descriptive_content(self) -> None:
        """`REQ-DATA-005` stated as an invariant over the table.

        The absolute values are provisional pending `DEC-005`. **This ordering is
        not** — it is the requirement itself, so it is asserted as a property that
        survives whatever the numbers become.
        """
        descriptive = POLICIES[FieldClass.DESCRIPTION].max_age
        for faster in (FieldClass.HOURS, FieldClass.DISRUPTION):
            assert POLICIES[faster].max_age < descriptive

    def test_the_same_age_gets_different_verdicts_in_different_classes(self) -> None:
        """Field-specific, demonstrated rather than asserted: one day old is expired
        hours, and a perfectly good description."""
        a_day = timedelta(days=1)
        assert (
            assess(fact(FieldClass.HOURS, observed_ago=a_day), now=NOW, used_for=TRIP).verdict
            is Verdict.EXPIRED
        )
        assert (
            assess(fact(FieldClass.DESCRIPTION, observed_ago=a_day), now=NOW, used_for=TRIP).verdict
            is Verdict.FRESH
        )

    def test_exactly_at_the_threshold_is_still_fresh(self) -> None:
        """Which side of the boundary is inclusive, pinned.

        "Expires after six hours" should not expire *at* six hours, and an exclusive
        bound makes the verdict depend on clock resolution — the same fact assessed
        twice a microsecond apart would flip. Inclusive, and one microsecond past is
        not.
        """
        limit = POLICIES[FieldClass.HOURS].max_age
        exactly = assess(fact(FieldClass.HOURS, observed_ago=limit), now=NOW, used_for=TRIP)
        just_past = assess(
            fact(FieldClass.HOURS, observed_ago=limit + timedelta(microseconds=1)),
            now=NOW,
            used_for=TRIP,
        )
        assert exactly.verdict is Verdict.FRESH
        assert exactly.staleness_ratio == 1.0
        assert just_past.verdict is Verdict.EXPIRED

    def test_an_unregistered_field_class_raises_rather_than_defaulting(self) -> None:
        """A lenient default is how a closure inherits a description's threshold."""
        with pytest.raises(FreshnessError, match="no freshness policy"):
            policy_for("rumour")  # type: ignore[arg-type]

    def test_a_policy_without_a_rationale_is_refused(self) -> None:
        with pytest.raises(FreshnessError, match="cannot be reviewed"):
            FreshnessPolicy(
                field_class=FieldClass.PRICE,
                max_age=timedelta(days=1),
                severity=Severity.ADVISORY,
                rationale="   ",
            )


# --- block or degrade -----------------------------------------------------------


class TestCriticalStalenessBlocksAndOtherStalenessMarks:
    def test_stale_hours_block_the_option(self) -> None:
        """`REQ-EVID-005` allows blocking or lowering confidence. Hours block:
        reading them wrong is a hard-constraint violation, which is S1 here."""
        result = assess(
            fact(FieldClass.HOURS, observed_ago=timedelta(days=1)), now=NOW, used_for=TRIP
        )
        assert (result.verdict, result.blocks_option) == (Verdict.EXPIRED, True)

    def test_a_stale_price_is_marked_without_blocking(self) -> None:
        """Refusing every option with a week-old price refuses nearly everything.
        The fact is marked and the consumer lowers confidence."""
        result = assess(
            fact(FieldClass.PRICE, observed_ago=timedelta(days=30)), now=NOW, used_for=TRIP
        )
        assert (result.verdict, result.blocks_option) == (Verdict.STALE, False)

    def test_staleness_ratio_is_published_instead_of_a_confidence_multiplier(self) -> None:
        """How confidence falls with staleness is the scenario scorer's curve. A
        multiplier invented here would be a magic constant in the wrong module —
        `BUG-026`'s shape exactly."""
        result = assess(
            fact(FieldClass.PRICE, observed_ago=timedelta(days=14)), now=NOW, used_for=TRIP
        )
        assert result.staleness_ratio == pytest.approx(2.0)

    def test_the_module_stores_no_staleness_flag_and_no_confidence_constant(self) -> None:
        """The structural half of "computed at time of use".

        A stored boolean is wrong the moment the clock moves, and nothing announces
        when it became wrong. `assess` takes `now`; there is no field to go stale.
        """
        import freshness

        assert "now" in inspect.signature(freshness.assess).parameters
        for name in dir(Assessment):
            assert name not in {"is_stale", "stale", "expired_at", "confidence"}
        source = inspect.getsource(freshness)
        assert "confidence_multiplier" not in source
        assert "def is_stale" not in source


# --- refusals -------------------------------------------------------------------


class TestInputsAreRefusedNotRepaired:
    @pytest.mark.parametrize("field", ["observed_at", "effective_from"])
    def test_a_naive_timestamp_is_refused(self, field: str) -> None:
        kwargs: dict[str, object] = {
            "field_class": FieldClass.HOURS,
            "observed_at": NOW,
            "effective_from": NOW,
        }
        kwargs[field] = datetime(2026, 8, 18, 12, 0)  # noqa: DTZ001
        with pytest.raises(FreshnessError, match="timezone-aware"):
            TemporalFact(**kwargs)  # type: ignore[arg-type]

    def test_a_window_that_ends_before_it_starts_is_refused(self) -> None:
        """It covers nothing, so every applicability check would fail against it and
        the reason would look like a data problem somewhere else."""
        with pytest.raises(FreshnessError, match="precedes effective_from"):
            TemporalFact(
                field_class=FieldClass.HOURS,
                observed_at=NOW,
                effective_from=NOW,
                effective_to=NOW - timedelta(days=1),
            )

    def test_an_assessment_without_a_reason_is_refused(self) -> None:
        with pytest.raises(FreshnessError, match="states why"):
            Assessment(
                verdict=Verdict.FRESH,
                field_class=FieldClass.HOURS,
                age=timedelta(0),
                max_age=timedelta(hours=6),
                severity=Severity.BLOCKING,
                reason="",
            )

    def test_a_naive_now_is_refused(self) -> None:
        with pytest.raises(FreshnessError, match="now must be timezone-aware"):
            assess(
                fact(FieldClass.HOURS, observed_ago=timedelta(hours=1)),
                now=datetime(2026, 8, 18, 12, 0),  # noqa: DTZ001
                used_for=TRIP,
            )
