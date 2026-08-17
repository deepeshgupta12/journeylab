"""Forecasts, normals, alerts and withdrawal — TST-DATA-005 · STEP-005.03.

WHAT THESE PROTECT
    Every failure here ends as a confident claim about the future that nobody
    marked as uncertain:

      a normal presented as a forecast   REQ-EVID-003 — an estimate rendered as
                                         confirmed
      a point value with no spread       the simulator treats it as certain, and
                                         REQ-CONS-006's seed samples nothing
      an objective silently dropped      the user compares on a criterion they
                                         believe was applied (REQ-DATA-003)
      an unknown alert level downgraded  a national weather service's judgement
                                         replaced by ours, invisibly
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from places.licence import KNOWN_LICENCES, METEOSWISS
from weather.alerts import AlertSeverity, WeatherAlert, parse_severity
from weather.degradation import (
    ObjectiveWithdrawn,
    WithdrawalReason,
    withdraw_weather_objective,
)
from weather.forecast import (
    ICON_CH1_EPS_HORIZON,
    ICON_CH2_EPS_HORIZON,
    ClimateNormal,
    Forecast,
    Uncertainty,
    ValueKind,
    WeatherError,
    outlook_for,
)

ISSUED = datetime(2026, 8, 14, 6, 0, tzinfo=UTC)


def a_forecast(**kw: object) -> Forecast:
    defaults: dict[str, object] = {
        "variable": "temperature_2m",
        "value": 18.0,
        "unit": "C",
        "uncertainty": Uncertainty(16.0, 20.0, ensemble_members=21),
        "issued_at": ISSUED,
        "valid_at": ISSUED + timedelta(days=2),
        "source_id": "meteoswiss",
    }
    return Forecast(**{**defaults, **kw})  # type: ignore[arg-type]


def a_normal(**kw: object) -> ClimateNormal:
    defaults: dict[str, object] = {
        "variable": "temperature_2m",
        "value": 17.0,
        "unit": "C",
        "uncertainty": Uncertainty(11.0, 24.0),
        "based_on_years": 30,
        "source_id": "meteoswiss",
    }
    return ClimateNormal(**{**defaults, **kw})  # type: ignore[arg-type]


# --- a point forecast is not an input to a simulation -------------------------


class TestUncertaintyIsMandatory:
    def test_a_forecast_cannot_be_built_without_uncertainty(self) -> None:
        """No default, because a default here is a fabricated confidence interval."""
        with pytest.raises(TypeError):
            Forecast(  # type: ignore[call-arg]
                variable="temperature_2m",
                value=18.0,
                unit="C",
                issued_at=ISSUED,
                valid_at=ISSUED + timedelta(days=1),
                source_id="meteoswiss",
            )

    def test_a_value_outside_its_own_interval_is_refused(self) -> None:
        """Not a wide interval — an inconsistent one, and it would make every
        downstream uncertainty calculation nonsense."""
        with pytest.raises(WeatherError, match="outside its own uncertainty"):
            a_forecast(value=30.0)

    def test_a_reversed_interval_is_refused(self) -> None:
        with pytest.raises(WeatherError, match="exceeds upper"):
            Uncertainty(20.0, 16.0)

    def test_a_single_member_ensemble_is_refused(self) -> None:
        """A one-run 'ensemble' is a point forecast wearing a spread's clothes."""
        with pytest.raises(WeatherError, match="at least 2 members"):
            Uncertainty(16.0, 20.0, ensemble_members=1)

    def test_member_count_is_retained(self) -> None:
        """A spread over 3 members and one over 51 are different evidence."""
        assert a_forecast().uncertainty.ensemble_members == 21


# --- REQ-EVID-003: a normal is not a forecast ---------------------------------


class TestNormalIsNotAForecast:
    def test_they_are_different_types(self) -> None:
        """The whole mechanism. A consumer written only for `Forecast` fails to
        typecheck rather than silently presenting a 30-year average as Tuesday."""
        assert a_forecast().kind is ValueKind.FORECAST
        assert a_normal().kind is ValueKind.CLIMATE_NORMAL
        assert not isinstance(a_normal(), Forecast)

    def test_beyond_the_horizon_returns_a_normal_marked_as_such(self) -> None:
        outlook = outlook_for(
            ISSUED + timedelta(days=20),
            forecast=a_forecast(),
            normal=a_normal(),
            issued_at=ISSUED,
            horizon=ICON_CH2_EPS_HORIZON,
        )
        assert outlook.kind is ValueKind.CLIMATE_NORMAL
        assert outlook.beyond_horizon is True

    def test_within_the_horizon_returns_the_forecast(self) -> None:
        outlook = outlook_for(
            ISSUED + timedelta(days=2),
            forecast=a_forecast(),
            normal=a_normal(),
            issued_at=ISSUED,
            horizon=ICON_CH2_EPS_HORIZON,
        )
        assert outlook.kind is ValueKind.FORECAST
        assert outlook.beyond_horizon is False

    def test_a_missing_forecast_falls_back_within_the_horizon_too(self) -> None:
        """A provider that returns nothing for a variable is not a reason to
        invent one; it is the same substitution, and it is marked the same way."""
        outlook = outlook_for(
            ISSUED + timedelta(days=1),
            forecast=None,
            normal=a_normal(),
            issued_at=ISSUED,
            horizon=ICON_CH2_EPS_HORIZON,
        )
        assert outlook.kind is ValueKind.CLIMATE_NORMAL
        assert outlook.beyond_horizon is True

    def test_the_horizon_is_measured_from_issue_not_from_now(self) -> None:
        """A forecast issued long ago, for a date far beyond its own horizon.

        THIS TEST EXISTS IN THIS SHAPE BECAUSE MUTATION TESTING BROKE THE FIRST ONE.
        The original used timestamps near the real present, so `moment - issued_at`
        and `moment - now()` agreed and a mutant that measured from wall-clock
        survived. Dates well in the past separate them: measured from issue this is
        19 days out and beyond the horizon; measured from now it is in the past and
        would read as within it.

        The property is that **a stored forecast gives the same answer whenever it
        is read** — otherwise the same record is valid this morning and invalid
        this afternoon.
        """
        old_issue = datetime(2026, 1, 1, 6, 0, tzinfo=UTC)
        far_moment = datetime(2026, 1, 20, 12, 0, tzinfo=UTC)
        assert far_moment - old_issue > ICON_CH2_EPS_HORIZON

        outlook = outlook_for(
            far_moment,
            forecast=a_forecast(issued_at=old_issue, valid_at=far_moment),
            normal=a_normal(),
            issued_at=old_issue,
            horizon=ICON_CH2_EPS_HORIZON,
        )
        assert outlook.beyond_horizon is True
        assert outlook.kind is ValueKind.CLIMATE_NORMAL

    def test_a_short_record_cannot_be_called_a_normal(self) -> None:
        with pytest.raises(WeatherError, match="too short a record"):
            a_normal(based_on_years=3)

    def test_a_forecast_valid_before_it_was_issued_is_refused(self) -> None:
        with pytest.raises(WeatherError, match="precedes issued_at"):
            a_forecast(valid_at=ISSUED - timedelta(hours=1))

    def test_naive_timestamps_are_refused(self) -> None:
        with pytest.raises(WeatherError, match="timezone-aware"):
            a_forecast(issued_at=datetime(2026, 8, 14, 6, 0))  # noqa: DTZ001


# --- REQ-DATA-003: withdrawal is disclosed, never silent ----------------------


class TestObjectiveWithdrawal:
    def test_a_withdrawn_objective_carries_no_score(self) -> None:
        """A nullable score is one `None` check away from ranking as zero — and
        zero is a position in the ranking, which is the silent degradation."""
        withdrawn = withdraw_weather_objective(WithdrawalReason.PROVIDER_UNAVAILABLE)
        assert not hasattr(withdrawn, "score")

    def test_every_reason_produces_user_facing_copy(self) -> None:
        """ "Disclosed" is the half of the rule that makes withdrawal honest rather
        than merely safe, so every reason must be sayable."""
        for reason in WithdrawalReason:
            withdrawn = withdraw_weather_objective(reason)
            assert len(withdrawn.disclosure) > 40
            assert withdrawn.reason is reason

    def test_the_reasons_are_distinguishable_not_one_string(self) -> None:
        """A circuit-breaker outage, an exceeded horizon and an uncovered region
        need different copy and different remedies."""
        texts = {withdraw_weather_objective(r).disclosure for r in WithdrawalReason}
        assert len(texts) == len(list(WithdrawalReason))

    def test_a_withdrawal_without_disclosure_is_refused(self) -> None:
        with pytest.raises(ValueError, match="silent degradation"):
            ObjectiveWithdrawn(
                objective="weather_resilient",
                reason=WithdrawalReason.PROVIDER_UNAVAILABLE,
                disclosure="   ",
            )

    def test_the_horizon_disclosure_says_a_normal_is_not_a_forecast(self) -> None:
        """The copy has to carry REQ-EVID-003, not just the type system."""
        text = withdraw_weather_objective(WithdrawalReason.BEYOND_FORECAST_HORIZON).disclosure
        assert "not a forecast" in text.lower()


# --- alerts -------------------------------------------------------------------


class TestAlerts:
    def test_known_severities_pass_through(self) -> None:
        assert parse_severity("Severe") is AlertSeverity.SEVERE
        assert parse_severity("extreme") is AlertSeverity.EXTREME

    def test_an_unrecognised_level_is_unknown_never_downgraded(self) -> None:
        """Mapping it to the nearest neighbour substitutes our judgement for a
        national weather service's, invisibly, where being wrong has physical
        consequences."""
        assert parse_severity("code-purple") is AlertSeverity.UNKNOWN
        assert parse_severity("") is AlertSeverity.UNKNOWN

    def test_no_unrecognised_input_is_ever_mapped_to_a_real_severity(self) -> None:
        """The property, rather than the tautology.

        My first version asserted `UNKNOWN is not MINOR`, which mypy correctly
        flagged as a non-overlapping identity check — statically always true, so it
        could never fail and tested nothing. That is the vacuous-assertion pattern
        this repository has hit repeatedly (BUG-020, BUG-021); this time a type
        checker caught it rather than a later reader.

        What matters is behavioural: nothing a provider can send gets silently
        promoted into a level a meteorological service did not assign.
        """
        for raw in ("code-purple", "", "  ", "verySevere", "1", "critical", "orange"):
            assert parse_severity(raw) is AlertSeverity.UNKNOWN, raw

    def test_an_alert_is_active_between_onset_and_expiry(self) -> None:
        alert = WeatherAlert(
            headline="Thunderstorms",
            severity=AlertSeverity.SEVERE,
            onset=ISSUED,
            expires=ISSUED + timedelta(hours=6),
            source_id="meteoswiss",
        )
        assert not alert.active_at(ISSUED - timedelta(hours=1))
        assert alert.active_at(ISSUED + timedelta(hours=1))
        assert not alert.active_at(ISSUED + timedelta(hours=7))

    def test_an_absent_expiry_is_open_ended_not_expired(self) -> None:
        """The same distinction temporal-validity.json makes, and the safe reading
        for a warning."""
        alert = WeatherAlert(
            headline="Avalanche risk",
            severity=AlertSeverity.EXTREME,
            onset=ISSUED,
            expires=None,
            source_id="meteoswiss",
        )
        assert alert.active_at(ISSUED + timedelta(days=30))

    def test_a_reversed_validity_is_refused(self) -> None:
        with pytest.raises(ValueError, match="precedes onset"):
            WeatherAlert(
                headline="x",
                severity=AlertSeverity.MINOR,
                onset=ISSUED,
                expires=ISSUED - timedelta(hours=1),
                source_id="meteoswiss",
            )


# --- the licence, which is why this is MeteoSwiss and not Open-Meteo ----------


class TestWeatherLicence:
    def test_meteoswiss_is_registered_and_commercial(self) -> None:
        assert METEOSWISS.commercial_use_permitted
        assert "meteoswiss" in KNOWN_LICENCES

    def test_attribution_is_recorded(self) -> None:
        assert METEOSWISS.attribution_required
        assert "MeteoSwiss" in METEOSWISS.attribution_text


class TestBug026TheHorizonHasNoDefault:
    """BUG-026 — a wrong default is worse than no default.

    `DEFAULT_HORIZON = timedelta(days=10)` shipped in STEP-005.03 on the reasoning
    that ten days is the usual limit for deterministic skill. The first live check
    of MeteoSwiss established the real figures, and neither is ten days:
    ICON-CH1-EPS is 33 hours with 11 members, ICON-CH2-EPS is 120 hours with 21.

    A ten-day default would have returned a `Forecast` for a moment the provider
    cannot forecast at all — the exact REQ-EVID-003 violation this module exists to
    prevent, produced by the module's own default rather than a caller's mistake.
    """

    def test_the_provider_horizons_match_the_published_figures(self) -> None:
        """Pinned so a future edit cannot quietly restore a plausible wrong number."""
        assert ICON_CH1_EPS_HORIZON == timedelta(hours=33)
        assert ICON_CH2_EPS_HORIZON == timedelta(hours=120)

    def test_neither_horizon_is_ten_days(self) -> None:
        """The specific wrong value, named. This is the regression."""
        assert ICON_CH1_EPS_HORIZON < timedelta(days=10)
        assert ICON_CH2_EPS_HORIZON < timedelta(days=10)

    def test_a_horizon_must_be_supplied(self) -> None:
        """No default at all — the caller states the provider's limit or fails."""
        with pytest.raises(TypeError):
            outlook_for(  # type: ignore[call-arg]
                ISSUED + timedelta(days=2),
                forecast=a_forecast(),
                normal=a_normal(),
                issued_at=ISSUED,
            )

    def test_a_non_positive_horizon_is_refused(self) -> None:
        for bad in (timedelta(0), timedelta(hours=-1)):
            with pytest.raises(WeatherError, match="horizon must be positive"):
                outlook_for(
                    ISSUED + timedelta(hours=1),
                    forecast=a_forecast(),
                    normal=a_normal(),
                    issued_at=ISSUED,
                    horizon=bad,
                )

    def test_day_seven_is_beyond_meteoswiss_and_returns_a_normal(self) -> None:
        """The bug's concrete consequence, asserted directly. Under the old ten-day
        default this returned a forecast for a day MeteoSwiss cannot forecast."""
        outlook = outlook_for(
            ISSUED + timedelta(days=7),
            forecast=a_forecast(valid_at=ISSUED + timedelta(days=7)),
            normal=a_normal(),
            issued_at=ISSUED,
            horizon=ICON_CH2_EPS_HORIZON,
        )
        assert outlook.kind is ValueKind.CLIMATE_NORMAL
        assert outlook.beyond_horizon is True

    def test_the_ensemble_member_counts_are_representable(self) -> None:
        """11 and 21 members: the live check confirmed MeteoSwiss publishes an
        ensemble, which is what makes `.03`'s mandatory uncertainty satisfiable at
        all rather than a requirement no provider could meet."""
        for members in (11, 21):
            assert Uncertainty(16.0, 20.0, ensemble_members=members).ensemble_members == members
