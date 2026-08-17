"""Forecasts, normals and the line between them — STEP-005.03 (REQ-DATA-005, REQ-EVID-003).

TWO DISTINCTIONS, AND BOTH ARE TYPES RATHER THAN FLAGS

1. A NORMAL IS NOT A FORECAST.
    Beyond the forecast horizon the honest answer is a climatological normal — what
    August usually looks like in Zurich. That is a legitimate input and it is **not
    a prediction about next Tuesday**.

    `REQ-EVID-003`: an estimate is never rendered as confirmed. Returning a normal
    through the same type as a forecast is precisely how it gets rendered as one,
    so `ClimateNormal` and `Forecast` are separate types. A consumer must name
    which it is handling, and the compiler makes it.

2. A POINT FORECAST IS NOT AN INPUT TO A SIMULATION.
    `18°C` tells a simulator nothing about how wrong it might be, so the simulator
    treats it as certain — and this product's entire claim is comparing **feasible
    futures**, plural, under uncertainty. `REQ-CONS-006` wants reproducibility from
    inputs and a seed; a point estimate silently removes the distribution the seed
    was meant to sample.

    So `Forecast` cannot be constructed without uncertainty. There is no default,
    because a default here is a fabricated confidence interval.

WHAT THIS MODULE WILL NOT DO
    It will not widen a bare point value into "probably ±2°". That would be
    inventing the uncertainty the requirement exists to preserve — the weather
    equivalent of the coerce that `schema_gate` refuses.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


class WeatherError(ValueError):
    """A weather value could not be constructed honestly."""


class ValueKind(enum.StrEnum):
    """What kind of claim a value is. Never inferred from context."""

    FORECAST = "forecast"
    #: A climatological average. Says what is typical, not what will happen.
    CLIMATE_NORMAL = "climate_normal"
    OBSERVATION = "observation"


@dataclass(frozen=True, slots=True)
class Uncertainty:
    """How wrong the value might be, from the provider — never from us.

    Either an ensemble spread or a stated confidence interval. Both are recorded
    with the member count when there is one, because a spread over 3 members and a
    spread over 51 are different evidence and averaging them is how a simulation
    acquires false precision.
    """

    lower: float
    upper: float
    #: Ensemble members behind the spread, when the provider publishes one.
    ensemble_members: int | None = None

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise WeatherError(f"uncertainty lower {self.lower} exceeds upper {self.upper}")
        if self.ensemble_members is not None and self.ensemble_members < 2:
            raise WeatherError(
                "an ensemble needs at least 2 members; a single run is a point "
                "forecast wearing a spread's clothes"
            )

    @property
    def width(self) -> float:
        return self.upper - self.lower


@dataclass(frozen=True, slots=True)
class Forecast:
    """A prediction for a moment, with its uncertainty and its issue time.

    `issued_at` matters as much as `valid_at`: two forecasts for the same afternoon
    issued six hours apart are different evidence, and `REQ-EVID-001`'s
    "observed time, not fetch time" distinction is meaningless without it.
    """

    variable: str
    value: float
    unit: str
    uncertainty: Uncertainty
    issued_at: datetime
    valid_at: datetime
    source_id: str

    def __post_init__(self) -> None:
        for name, moment in (("issued_at", self.issued_at), ("valid_at", self.valid_at)):
            if moment.tzinfo is None:
                raise WeatherError(f"{name} must be timezone-aware")
        if self.valid_at < self.issued_at:
            raise WeatherError(
                "valid_at precedes issued_at — a forecast cannot be for a moment before it was made"
            )
        if not (self.uncertainty.lower <= self.value <= self.uncertainty.upper):
            raise WeatherError(
                f"the value {self.value} lies outside its own uncertainty "
                f"[{self.uncertainty.lower}, {self.uncertainty.upper}]. That is not a "
                f"wide interval, it is an inconsistent one"
            )

    @property
    def kind(self) -> ValueKind:
        return ValueKind.FORECAST

    @property
    def lead_time(self) -> timedelta:
        return self.valid_at - self.issued_at


@dataclass(frozen=True, slots=True)
class ClimateNormal:
    """What this variable typically does here at this time of year.

    A SEPARATE TYPE, and that is the whole point. It is returned when a moment is
    beyond the forecast horizon, and a consumer that has not been written to handle
    it will fail to compile rather than quietly present a 30-year average as
    tomorrow's weather (`REQ-EVID-003`).
    """

    variable: str
    value: float
    unit: str
    uncertainty: Uncertainty
    #: Years of record behind the average. A "normal" from three years is not one.
    based_on_years: int
    source_id: str

    def __post_init__(self) -> None:
        if self.based_on_years < 10:
            raise WeatherError(
                f"{self.based_on_years} years is too short a record to call a normal. "
                f"Presenting it as one would be an estimate dressed as a baseline "
                f"(REQ-EVID-003)."
            )

    @property
    def kind(self) -> ValueKind:
        return ValueKind.CLIMATE_NORMAL


# HOW FAR AHEAD A FORECAST IS MEANINGFUL — AND WHY THERE IS NO DEFAULT
#
#   There was one, and it was wrong. `DEFAULT_HORIZON = timedelta(days=10)` shipped
#   in STEP-005.03 on the reasoning that ten days is "the usual limit for
#   deterministic skill". The first live check of MeteoSwiss (STEP-005.06 recon,
#   `BUG-026`) established the real numbers, and neither is ten days:
#
#       ICON-CH1-EPS    33 hours,  11 ensemble members
#       ICON-CH2-EPS   120 hours,  21 ensemble members
#
#   A ten-day default would have let a day-seven request return a `Forecast` for a
#   moment the provider cannot forecast at all — producing exactly the
#   `REQ-EVID-003` violation this module exists to prevent, and producing it from
#   the module's own default rather than from a caller's mistake.
#
#   So the horizon is now a REQUIRED argument. A plausible-looking default is worse
#   than no default here: it is the failure mode that does not announce itself.
#   Named constants exist for the provider `ADR-016` chose, and a new provider must
#   state its own rather than inheriting Switzerland's.

#: MeteoSwiss ICON-CH1-EPS — 1 km grid, 11 members, refreshed 8 times daily.
ICON_CH1_EPS_HORIZON = timedelta(hours=33)

#: MeteoSwiss ICON-CH2-EPS — 2.1 km grid, 21 members. The longer of the two.
ICON_CH2_EPS_HORIZON = timedelta(hours=120)


@dataclass(frozen=True, slots=True)
class Outlook:
    """What we can honestly say about a moment: a forecast, or a normal, and which."""

    value: Forecast | ClimateNormal
    #: True when the horizon was exceeded and a normal was substituted. Surfaced so
    #: the interface can say so rather than the substitution being invisible.
    beyond_horizon: bool

    @property
    def kind(self) -> ValueKind:
        return self.value.kind


def outlook_for(
    moment: datetime,
    *,
    forecast: Forecast | None,
    normal: ClimateNormal,
    issued_at: datetime,
    horizon: timedelta,
) -> Outlook:
    """The honest answer for a moment, forecast or normal.

    The horizon is checked against `issued_at` rather than "now", because a forecast
    issued yesterday for eleven days out is beyond the horizon whatever time it is
    when someone asks. Using wall-clock time here would make the same stored
    forecast valid or invalid depending on when it was read.

    `horizon` is **required** and deliberately has no default — see the note above
    the provider constants. `BUG-026` was a wrong default, not a wrong caller.
    """
    if horizon <= timedelta(0):
        raise WeatherError("horizon must be positive")
    if moment.tzinfo is None or issued_at.tzinfo is None:
        raise WeatherError("both moment and issued_at must be timezone-aware")

    if moment - issued_at > horizon or forecast is None:
        return Outlook(value=normal, beyond_horizon=True)
    return Outlook(value=forecast, beyond_horizon=False)


def now_utc() -> datetime:
    return datetime.now(UTC)
