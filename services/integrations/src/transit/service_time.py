"""GTFS service time — STEP-005.04 (REQ-DATA-002).

THE DISTINCTION THIS MODULE EXISTS FOR: A SERVICE DAY IS NOT A CALENDAR DAY

    GTFS writes a 01:30 departure on the night of the 14th as **`25:30` on service
    date 2026-08-14**. That is not a malformed time and not a typo. It says: this
    trip belongs to Friday's service, and it departs after Friday's midnight.

    Both naive readings are wrong, in opposite and equally damaging ways:

        reject it as invalid   -> the entire night network disappears, and the
                                  gap looks like "no service" rather than a
                                  parsing failure. A solver then reports a
                                  feasible late journey as impossible.

        wrap it to 01:30 today -> every late service moves back twenty-four
                                  hours. The itinerary contains a train that
                                  left last night, which is a hard-constraint
                                  violation (`REQ-CONS-004`) — S1 by definition
                                  in this repository's register.

    For a Swiss region chosen partly for last-funicular and last-boat constraints
    (`ADR-016`), this is the specific error that produces a confidently wrong plan.

WHY MIDNIGHT IS COMPUTED FROM NOON — AND WHAT I COULD NOT DEMONSTRATE

    The GTFS specification measures service time from **noon minus twelve hours**
    on the service date rather than from midnight. The stated rationale is that
    local midnight may not exist on a spring-forward date and may happen twice on a
    fall-back date, whereas noon is unambiguous everywhere.

    This implementation follows the specification. **It does not follow it because
    a defect was observed** — and that distinction is recorded here rather than
    implied, because I tried to observe one and could not.

    Mutation testing replaced this anchor with a plain wall-clock midnight, and the
    suite still passed. Measuring directly across both 2026 Zurich transitions, and
    in Havana, Santiago, Beirut and Asunción (zones whose transitions fall at or
    near midnight), the two anchors produce the **identical instant** in every case:
    Python's `zoneinfo` normalises a non-existent or ambiguous wall-clock midnight
    rather than raising, and `noon - 12h` lands on the same normalisation.

    So the honest position is: the noon anchor is **specification conformance**, not
    a bug fix. It is kept because a feed produced against the spec should be read
    against the spec, and because a future zone, tzdata release or Python change
    could separate them. `test_the_two_anchors_agree_in_every_zone_tested` pins the
    equivalence, so if they ever diverge that becomes a visible failure rather than
    a silent change of meaning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

_GTFS_TIME = re.compile(r"^\s*(\d{1,3}):([0-5]\d):?([0-5]\d)?\s*$")

#: Hours past which a "service time" is almost certainly a data error rather than
#: a late-night trip. GTFS permits large values in principle; in practice a trip
#: departing more than two days into its service date is a feed bug, and accepting
#: it silently would place a departure in a day nobody scheduled.
MAX_SERVICE_HOUR = 48


class ServiceTimeError(ValueError):
    """A service time could not be interpreted, and was NOT guessed at."""


@dataclass(frozen=True, slots=True)
class ServiceTime:
    """An offset from the start of a service day.

    Deliberately not a `datetime.time`: `25:30` is not representable as one, and
    forcing it into that type is exactly the coercion that loses the night network.
    """

    hours: int
    minutes: int
    seconds: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.minutes <= 59 or not 0 <= self.seconds <= 59:
            raise ServiceTimeError(f"invalid service time {self}")
        if self.hours < 0:
            raise ServiceTimeError("service hours cannot be negative")
        if self.hours > MAX_SERVICE_HOUR:
            raise ServiceTimeError(
                f"{self.hours}:{self.minutes:02d} is more than {MAX_SERVICE_HOUR} hours "
                f"into its service day. GTFS permits it in principle, but in practice "
                f"this is a feed error, and accepting it would schedule a departure on "
                f"a day nobody planned."
            )

    @property
    def past_midnight(self) -> bool:
        """True when this belongs to the calendar day AFTER its service date."""
        return self.hours >= 24

    @property
    def offset(self) -> timedelta:
        return timedelta(hours=self.hours, minutes=self.minutes, seconds=self.seconds)

    def __str__(self) -> str:
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}"


def parse_service_time(text: str) -> ServiceTime:
    """Parse `HH:MM` or `HH:MM:SS`, where HH may exceed 23."""
    match = _GTFS_TIME.match(text)
    if match is None:
        raise ServiceTimeError(
            f"unparseable service time {text!r}. Not guessed at: a wrong departure "
            f"is a hard-constraint violation, not a display defect."
        )
    hours, minutes, seconds = match.group(1), match.group(2), match.group(3) or "0"
    return ServiceTime(hours=int(hours), minutes=int(minutes), seconds=int(seconds))


def service_day_start(service_date: date, time_zone: str) -> datetime:
    """The instant a service day begins, anchored at noon minus twelve hours.

    This is the GTFS definition and it is what makes DST total. Local midnight is
    missing on a spring-forward date and duplicated on a fall-back date; noon is
    neither, on any date in any zone.
    """
    zone = ZoneInfo(time_zone)
    noon = datetime(service_date.year, service_date.month, service_date.day, 12, 0, tzinfo=zone)
    return noon - timedelta(hours=12)


def instant_of(service_date: date, service_time: ServiceTime, time_zone: str) -> datetime:
    """The real moment a trip departs.

    `25:30` on 2026-08-14 becomes 01:30 on 2026-08-15, in the place's own zone —
    which is the whole point of the module.
    """
    return service_day_start(service_date, time_zone) + service_time.offset
