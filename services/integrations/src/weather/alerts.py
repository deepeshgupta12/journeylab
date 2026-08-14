"""Weather alerts — STEP-005.03.

SEVERITY IS THE PROVIDER'S, NOT OURS
    An alert arrives with a severity the issuing meteorological service assigned.
    Re-deriving it from the text, or mapping an unknown level to "probably minor",
    substitutes our judgement for a national weather service's — and does it
    invisibly, in the one part of the product where being wrong has physical
    consequences.

    So an unrecognised severity is `UNKNOWN` and is **never downgraded**. A
    consumer deciding what to surface must handle it explicitly; treating unknown
    as low is how a red warning becomes a footnote.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class AlertSeverity(enum.StrEnum):
    """CAP-style levels, plus an honest fallback."""

    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"
    #: The provider used a level we do not recognise. NOT a synonym for minor.
    UNKNOWN = "unknown"


#: Levels we accept verbatim. Anything else becomes UNKNOWN rather than the
#: nearest neighbour, for the reason in the module docstring.
_KNOWN = {s.value: s for s in AlertSeverity if s is not AlertSeverity.UNKNOWN}


@dataclass(frozen=True, slots=True)
class WeatherAlert:
    headline: str
    severity: AlertSeverity
    onset: datetime
    expires: datetime | None
    source_id: str

    def __post_init__(self) -> None:
        if self.onset.tzinfo is None:
            raise ValueError("onset must be timezone-aware")
        if self.expires is not None:
            if self.expires.tzinfo is None:
                raise ValueError("expires must be timezone-aware")
            if self.expires < self.onset:
                raise ValueError("expires precedes onset")

    def active_at(self, moment: datetime) -> bool:
        if moment.tzinfo is None:
            raise ValueError("moment must be timezone-aware")
        if moment < self.onset:
            return False
        # An absent expiry is OPEN-ENDED, not expired — the same distinction
        # temporal-validity.json makes, and the safe reading for a warning.
        return self.expires is None or moment <= self.expires


def parse_severity(raw: str) -> AlertSeverity:
    """Map a provider severity, refusing to guess at an unfamiliar one."""
    return _KNOWN.get(raw.strip().lower(), AlertSeverity.UNKNOWN)
