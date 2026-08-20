"""The three time axes, and arithmetic that survives a DST boundary — STEP-006.02.

WHY THIS MODULE EXISTS RATHER THAN A `WHERE` CLAUSE IN EACH CALLER

    `DATA_ARCHITECTURE` §3: *"The most common source of wrong travel plans is
    confusing 'when we learned it' with 'when it is true'."*

    Both axes are timestamps on the same row. Both compile. Both return plausible
    rows. A solver that filters on `observed_at` gets facts we happen to have
    fetched recently, which is not the same set as the facts that are true during
    the trip — and the difference only shows up as an itinerary built on last
    summer's timetable.

    So there is no general-purpose time filter here. There is `effective_during`,
    which is what a solver wants, and `observed_since`, which is what a freshness
    check wants, and each names its axis in its own name. A caller who reaches for
    the wrong one has to type the wrong word.

TWENTY-FOUR HOURS IS NOT ALWAYS A DAY

    In `Europe/Zurich`, 2026-03-29 has twenty-three hours and 2026-10-25 has
    twenty-five. That makes two different questions out of what looks like one:

      "same time tomorrow"   -> calendar arithmetic in local time. 09:00 to 09:00
                                across spring-forward is 23 elapsed hours, and the
                                traveller still expects 09:00.
      "twenty-four hours"    -> elapsed arithmetic. A duration a person spends, a
                                vehicle is rented for, or a solver reasons about.

    Both are correct answers to different questions, and the bug is answering one
    with the other. `same_local_time_next_day` and `elapsed_between` are separate
    functions because they are separate questions; a single `add_a_day` would have
    to pick one silently.

THE TRAP THAT CAUGHT THIS MODULE'S OWN AUTHOR

    Subtracting two aware datetimes that share a `tzinfo` object gives the **wall
    clock** difference, not the elapsed one. It is documented Python behaviour —
    "if both are aware and have the same tzinfo attribute, the common tzinfo is
    ignored" — and it is invisible, because the offsets on the two values are
    perfectly correct:

        a = datetime(2026, 3, 28, 9, 0, tzinfo=ZoneInfo("Europe/Zurich"))  # +01:00
        b = datetime(2026, 3, 29, 9, 0, tzinfo=ZoneInfo("Europe/Zurich"))  # +02:00
        b - a                                   -> 24:00:00   WRONG
        b.astimezone(UTC) - a.astimezone(UTC)   -> 23:00:00   right

    The first version of `elapsed_between` below was `return end - start`, which is
    the exact bug this module exists to prevent, written into the function whose
    whole job is preventing it. Every duration crossing a DST boundary would have
    been wrong by an hour, in the direction that makes a plan look feasible.

    So every subtraction here converts to UTC first, and a test asserts the value
    rather than the shape.

NAIVE DATETIMES ARE REFUSED, NOT INTERPRETED

    A naive timestamp is not "UTC by default" — it is a value whose meaning was
    lost before it arrived. Guessing a zone here would place a Swiss museum's
    closing time in London for half the year.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo


class TemporalError(ValueError):
    """A temporal input was refused, and NOT interpreted with a guessed zone."""


def require_aware(moment: datetime, *, label: str) -> datetime:
    """Every datetime crossing this boundary carries its zone, or is refused."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise TemporalError(
            f"{label} is naive. A timestamp without a zone is not 'UTC by default' — "
            f"it is a value whose meaning was lost before it got here, and guessing "
            f"would place a Swiss closing time in London for half the year"
        )
    return moment


def zone_of(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except Exception as exc:
        raise TemporalError(f"unknown IANA zone {name!r}") from exc


# --- the two axes, as two named questions ---------------------------------------


@dataclass(frozen=True, slots=True)
class AxisFilter:
    """A SQL fragment that names the axis it filters on.

    Returned rather than executed so the caller keeps its own transaction, and
    named rather than anonymous so a code review can see which question is being
    asked without reading the WHERE clause.
    """

    axis: str
    sql: str
    params: tuple[object, ...]


def effective_during(start: datetime, end: datetime) -> AxisFilter:
    """Facts true in the world during the window. **What a solver wants.**

    An open-ended `effective_to` is included: absent is not expired
    (`temporal-validity.json`). The comparison is half-open at the end so a fact
    ending exactly when the window opens does not count as covering it.
    """
    require_aware(start, label="start")
    require_aware(end, label="end")
    if end < start:
        raise TemporalError("an effective window cannot end before it starts")
    return AxisFilter(
        axis="effective",
        sql="(effective_from <= %s AND (effective_to IS NULL OR effective_to > %s))",
        params=(end, start),
    )


def observed_since(moment: datetime) -> AxisFilter:
    """Facts the source stated recently. **What a freshness check wants.**

    Never what a solver wants: a fact fetched this morning about last summer is
    observed recently and true never.
    """
    require_aware(moment, label="moment")
    return AxisFilter(axis="observed", sql="(observed_at >= %s)", params=(moment,))


def recorded_since(moment: datetime) -> AxisFilter:
    """Facts we wrote down recently. For audit and replay, not for planning.

    Separate from `observed_since` because the gap between them is our ingestion
    lag — ours to fix, and not evidence about the fact.
    """
    require_aware(moment, label="moment")
    return AxisFilter(axis="recorded", sql="(recorded_at >= %s)", params=(moment,))


# --- arithmetic that survives a DST boundary --------------------------------------


def same_local_time_next_day(moment: datetime, *, zone: str, days: int = 1) -> datetime:
    """ "Same time tomorrow", in the traveller's local reading.

    Calendar arithmetic in local time. Across spring-forward this advances 23
    elapsed hours and across autumn-back 25, which is exactly what a person means
    when they say they will be back at nine.

    Implemented by rebuilding the local wall-clock value rather than adding a
    `timedelta`: adding 24 hours to an aware datetime adds 24 *elapsed* hours, so
    09:00 becomes 10:00 on the day the clocks go forward.
    """
    tz = zone_of(zone)
    local = require_aware(moment, label="moment").astimezone(tz)
    target_date = local.date() + timedelta(days=days)
    return datetime.combine(target_date, local.time(), tzinfo=tz)


def elapsed_between(start: datetime, end: datetime) -> timedelta:
    """Real time that passes. **What a duration means to a solver or a rental.**

    Across spring-forward, 09:00 to 09:00 is 23 hours. That is the honest answer
    for anything measuring how long something takes, and the wrong answer for
    anything a person reads off a clock.
    """
    left = require_aware(start, label="start")
    right = require_aware(end, label="end")
    # Via UTC, deliberately. `right - left` on two values sharing a tzinfo object
    # returns the wall-clock difference and would report 24 hours for a 23-hour
    # spring-forward day. See the module docstring.
    return right.astimezone(UTC) - left.astimezone(UTC)


def local_calendar_days(start: datetime, end: datetime, *, zone: str) -> int:
    """Nights between two moments, counted on the local calendar.

    A trip that starts at 23:00 and ends at 01:00 the next day is one night and
    two hours; dividing elapsed time by 24 says zero. Hotel nights, day passes and
    "how many days is this trip" are all calendar questions.
    """
    tz = zone_of(zone)
    first = require_aware(start, label="start").astimezone(tz).date()
    last = require_aware(end, label="end").astimezone(tz).date()
    return (last - first).days


def is_dst_transition_day(day: datetime, *, zone: str) -> bool:
    """Whether the local day has other than twenty-four hours.

    Exposed because a test that only ever runs on ordinary days proves nothing
    about the days this module exists for.
    """
    tz = zone_of(zone)
    local = require_aware(day, label="day").astimezone(tz)
    midnight = datetime.combine(local.date(), datetime.min.time(), tzinfo=tz)
    next_midnight = datetime.combine(
        local.date() + timedelta(days=1), datetime.min.time(), tzinfo=tz
    )
    return (next_midnight.astimezone(UTC) - midnight.astimezone(UTC)) != timedelta(hours=24)
