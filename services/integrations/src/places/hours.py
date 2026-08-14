"""Opening hours as intervals — STEP-005.02 (REQ-DATA-005, TST-DATA-005).

THE DECISION THIS MODULE EXISTS TO GET RIGHT: UNKNOWN IS NOT CLOSED
    A place with no hours data and a place that is shut are different facts, and a
    boolean cannot hold both. Collapsing them breaks the solver in OPPOSITE
    directions, and both failures are ones this product exists to prevent:

        unknown treated as CLOSED  -> a feasible plan is reported infeasible.
                                      REQ-CONS-005: the user gets a conflict set
                                      for a constraint that does not exist.

        unknown treated as OPEN    -> an itinerary is built on a place that was
                                      shut. REQ-CONS-004 violation, which the bug
                                      register defines as **S1 by definition**.

    So `Availability` has three states and every consumer must handle the third.
    That is the whole reason this is a type rather than `list[Interval] | None`.

MIDNIGHT IS THE OTHER ONE
    `Fr 22:00-02:00` is one interval that ends on Saturday. Stored naively it has
    start > end, and every comparison downstream silently reverses. It is split at
    midnight into two same-day intervals instead — so an interval always satisfies
    start < end, and no consumer needs to know the rule.

TIME ZONES ARE NOT OPTIONAL
    Every interval carries the place's IANA zone, and `Place.time_zone` is required
    in the contract for this reason. A naive local time is a bug that surfaces
    twice a year, in a product whose entire claim is that a plan is feasible.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

DAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
_DAY_INDEX = {day: i for i, day in enumerate(DAYS)}

_RULE = re.compile(
    r"^\s*(?P<days>[A-Za-z]{2}(?:\s*-\s*[A-Za-z]{2})?(?:\s*,\s*[A-Za-z]{2}(?:\s*-\s*[A-Za-z]{2})?)*)"
    r"\s+(?P<spans>\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}(?:\s*,\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})*)\s*$"
)


class HoursError(ValueError):
    """The hours string could not be parsed, and was NOT guessed at."""


class Availability(enum.StrEnum):
    """Why a place has no open interval at a moment — or whether we even know."""

    OPEN = "open"
    CLOSED = "closed"
    #: We hold no usable hours. **Never render this as either of the others.**
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Interval:
    """One opening span on one weekday, in the place's own zone."""

    day: int
    start: time
    end: time

    def __post_init__(self) -> None:
        if not 0 <= self.day <= 6:
            raise HoursError(f"day must be 0..6, got {self.day}")
        if self.start >= self.end:
            raise HoursError(
                f"an interval must satisfy start < end; got {self.start}-{self.end}. "
                f"A span crossing midnight is split into two, so this never happens "
                f"by construction — see split_at_midnight."
            )


@dataclass(frozen=True, slots=True)
class OpeningHours:
    """Parsed hours, or the explicit absence of them."""

    intervals: tuple[Interval, ...]
    time_zone: str
    #: True when the source said nothing. Distinct from an empty interval list,
    #: which means "we parsed it and it is never open".
    unknown: bool = False

    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.time_zone)


def unknown_hours(time_zone: str) -> OpeningHours:
    """The honest result when a source carries no hours."""
    return OpeningHours(intervals=(), time_zone=time_zone, unknown=True)


def _parse_days(text: str) -> list[int]:
    days: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            first, last = (p.strip()[:2].title() for p in part.split("-", 1))
            if first not in _DAY_INDEX or last not in _DAY_INDEX:
                raise HoursError(f"unknown day range {part!r}")
            start, end = _DAY_INDEX[first], _DAY_INDEX[last]
            # Wrapping ranges are real: `Sa-Mo` is the weekend plus Monday.
            days.extend([(start + offset) % 7 for offset in range(((end - start) % 7) + 1)])
        else:
            key = part[:2].title()
            if key not in _DAY_INDEX:
                raise HoursError(f"unknown day {part!r}")
            days.append(_DAY_INDEX[key])
    return sorted(set(days))


def _parse_time(text: str) -> tuple[time, bool]:
    """Returns the time and whether it was `24:00`, which is midnight *tomorrow*."""
    hour_text, minute_text = text.strip().split(":")
    hour, minute = int(hour_text), int(minute_text)
    if (hour, minute) == (24, 0):
        return time(0, 0), True
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise HoursError(f"invalid time {text!r}")
    return time(hour, minute), False


def split_at_midnight(day: int, start: time, end: time) -> list[Interval]:
    """One span, as intervals that never cross midnight.

    `Fr 22:00-02:00` becomes Friday 22:00-24:00 and Saturday 00:00-02:00. Every
    downstream comparison is then a plain `start <= t < end` with no special case,
    which is the point: the rule lives here once instead of in every consumer.
    """
    if start < end:
        return [Interval(day=day, start=start, end=end)]
    if start == end:
        raise HoursError(f"a zero-length span is not an opening: {start}-{end}")
    return [
        Interval(day=day, start=start, end=time(23, 59, 59)),
        Interval(day=(day + 1) % 7, start=time(0, 0), end=end),
    ]


def parse(text: str, *, time_zone: str) -> OpeningHours:
    """Parse a subset of the OSM `opening_hours` syntax.

    A SUBSET, DELIBERATELY, AND IT RAISES ON THE REST.
        The full grammar covers public holidays, sunset offsets, week numbers and
        month ranges. Implementing a half-correct version of that would produce
        confidently wrong hours, and wrong hours are a hard-constraint violation
        (`REQ-CONS-004`) rather than a display bug.

        So anything outside the supported subset raises `HoursError`, and the
        caller records the place as `unknown` — which the solver already has to
        handle. Refusing to parse is safe; guessing is not.
    """
    ZoneInfo(time_zone)  # raises for a bogus zone rather than storing it

    cleaned = text.strip()
    if not cleaned:
        raise HoursError("empty hours string")
    if cleaned.lower() in {"24/7", "24x7"}:
        return OpeningHours(
            intervals=tuple(
                Interval(day=d, start=time(0, 0), end=time(23, 59, 59)) for d in range(7)
            ),
            time_zone=time_zone,
        )

    intervals: list[Interval] = []
    for rule in (r for r in cleaned.split(";") if r.strip()):
        match = _RULE.match(rule)
        if match is None:
            raise HoursError(
                f"unsupported hours rule {rule.strip()!r}. This parser covers a "
                f"deliberate subset; the caller must record the place as UNKNOWN "
                f"rather than accept a guess (REQ-CONS-004)."
            )
        days = _parse_days(match.group("days"))
        for span in match.group("spans").split(","):
            start_text, end_text = span.split("-", 1)
            start, _ = _parse_time(start_text)
            end, end_is_midnight = _parse_time(end_text)
            if end_is_midnight:
                end = time(23, 59, 59)
            for day in days:
                intervals.extend(split_at_midnight(day, start, end))

    return OpeningHours(
        intervals=tuple(sorted(intervals, key=lambda i: (i.day, i.start))), time_zone=time_zone
    )


def availability_at(hours: OpeningHours, moment: datetime) -> Availability:
    """Whether the place is open at a moment, or whether we do not know.

    `moment` must be timezone-aware. A naive datetime is refused rather than
    assumed to be local: assuming is how a plan becomes wrong by an hour twice a
    year, and this product's claim is that the plan is feasible.
    """
    if moment.tzinfo is None:
        raise HoursError("moment must be timezone-aware")
    if hours.unknown:
        return Availability.UNKNOWN

    local = moment.astimezone(hours.zone())
    weekday = local.weekday()
    now = local.time()
    for interval in hours.intervals:
        if interval.day == weekday and interval.start <= now <= interval.end:
            return Availability.OPEN
    return Availability.CLOSED


@dataclass(frozen=True, slots=True)
class SeasonalHours:
    """Hours that apply only within an effective window (`REQ-DATA-005`).

    A mountain railway running May to October is the case this exists for, and it is
    why `TemporalValidity` in the contract carries `effective_from`/`effective_to`
    rather than a single timestamp: the hours are correct AND bounded.
    """

    hours: OpeningHours
    effective_from: date
    effective_to: date | None

    def __post_init__(self) -> None:
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise HoursError("effective_to precedes effective_from")

    def applies_on(self, day: date) -> bool:
        if day < self.effective_from:
            return False
        # An absent end is OPEN-ENDED, not expired — the same distinction
        # `temporal-validity.json` makes, and for the same reason.
        return self.effective_to is None or day <= self.effective_to


def availability_in_season(
    seasons: tuple[SeasonalHours, ...], moment: datetime, *, time_zone: str
) -> Availability:
    """Availability across seasonal windows.

    No applicable season means **UNKNOWN**, not closed. A railway with summer hours
    and no winter entry tells us nothing about January; reporting `CLOSED` would be
    inventing a fact the source never stated.
    """
    if moment.tzinfo is None:
        raise HoursError("moment must be timezone-aware")
    local_day = moment.astimezone(ZoneInfo(time_zone)).date()

    applicable = [s for s in seasons if s.applies_on(local_day)]
    if not applicable:
        return Availability.UNKNOWN

    results = [availability_at(s.hours, moment) for s in applicable]
    if Availability.OPEN in results:
        return Availability.OPEN
    # Overlapping seasons where one is unknown: unknown wins over closed, because
    # claiming closed would again be inventing a fact.
    if Availability.UNKNOWN in results:
        return Availability.UNKNOWN
    return Availability.CLOSED
