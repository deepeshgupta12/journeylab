"""What happens when weather is unavailable — STEP-005.03 (REQ-DATA-003, REQ-AI-007).

THE SUB-STEP'S RULE, AND WHY IT IS NOT AN ERROR PATH
    §5: "Provider down => `weather_resilient` objective withdrawn **and disclosed**."

    Three things could happen when the weather provider is down, and two of them
    are failures this product exists to prevent:

      score it anyway from normals   -> a scenario ranked "weather resilient" on a
                                        30-year average presented as a forecast.
                                        REQ-EVID-003.
      drop it silently               -> the user compares three scenarios on an
                                        objective they still believe was applied.
                                        Worse than the first, because nothing
                                        indicates anything changed.
      WITHDRAW IT AND SAY SO         -> the comparison is honestly narrower.

    So withdrawal is a **product state with a reason attached**, not an exception.
    An exception would be caught somewhere and turned into one of the other two.

WHY THE REASON IS STRUCTURED
    "Weather unavailable" is not enough for the interface to write an honest
    sentence. A circuit-breaker outage, an exceeded horizon and a region with no
    coverage lead to different user-facing copy and different remedies, and a
    single free-text string cannot be branched on.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class WithdrawalReason(enum.StrEnum):
    """Why an objective could not be scored. Each needs different copy."""

    PROVIDER_UNAVAILABLE = "provider_unavailable"
    BEYOND_FORECAST_HORIZON = "beyond_forecast_horizon"
    NO_COVERAGE_FOR_REGION = "no_coverage_for_region"


@dataclass(frozen=True, slots=True)
class ObjectiveWithdrawn:
    """An objective that will not be scored, and why.

    Carries no score field at all. A withdrawn objective with a nullable score is
    one `None` check away from being ranked as zero — and zero is a position in the
    ranking, which is exactly the silent degradation being prevented.
    """

    objective: str
    reason: WithdrawalReason
    #: Shown to the user. Required, because "disclosed" is the half of the rule
    #: that makes withdrawal honest rather than merely safe.
    disclosure: str

    def __post_init__(self) -> None:
        if not self.disclosure.strip():
            raise ValueError(
                f"{self.objective}: a withdrawal without a disclosure is a silent "
                f"degradation, which is the thing REQ-DATA-003 forbids"
            )


def withdraw_weather_objective(reason: WithdrawalReason) -> ObjectiveWithdrawn:
    """Withdraw `weather_resilient`, with copy a person can act on."""
    disclosures = {
        WithdrawalReason.PROVIDER_UNAVAILABLE: (
            "Weather data is unavailable, so these plans were not compared on "
            "weather resilience. Everything else was."
        ),
        WithdrawalReason.BEYOND_FORECAST_HORIZON: (
            "These dates are beyond the forecast range, so weather resilience was "
            "not scored. Typical conditions for the season are shown instead, and "
            "they are not a forecast."
        ),
        WithdrawalReason.NO_COVERAGE_FOR_REGION: (
            "No weather source covers this region, so weather resilience was not compared."
        ),
    }
    return ObjectiveWithdrawn(
        objective="weather_resilient",
        reason=reason,
        disclosure=disclosures[reason],
    )
