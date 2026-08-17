"""Service calendars and their exceptions — STEP-005.04 (REQ-DATA-002).

THE PRECEDENCE RULE, AND WHY GETTING IT BACKWARDS IS DANGEROUS

    GTFS describes when a service runs in two places:

        calendar.txt        a weekly pattern between two dates
        calendar_dates.txt  named dates that ADD or REMOVE service

    **An exception always wins over the pattern.** That is the specification, and
    the failure mode of getting it backwards is asymmetric:

        removal ignored -> the plan uses a train that does not run on Christmas
                           Day. A hard-constraint violation (`REQ-CONS-004`),
                           and the traveller is at a station.

        addition ignored -> a service that does run is invisible. The plan is
                           worse than necessary, and the user never learns why.

    The first is the one that strands somebody, so the rule is implemented as a
    lookup that consults exceptions FIRST and returns immediately — there is no
    path where the weekly pattern can override an explicit date.

WHY "NO INFORMATION" IS NOT "NOT RUNNING"
    Outside a calendar's date range this module returns `UNKNOWN`, not `False`.
    The same three-state discipline as places (`STEP-005.02`) and for the same
    reason: a feed that stops on 31 December says nothing about January, and
    answering "does not run" invents a fact that produces a false infeasibility.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date


class ServiceError(ValueError):
    """A calendar could not be interpreted."""


class Runs(enum.StrEnum):
    """Whether a service operates on a date — or whether the feed says."""

    YES = "yes"
    NO = "no"
    #: The date lies outside every calendar we hold. NOT the same as "no".
    UNKNOWN = "unknown"


class ExceptionType(enum.IntEnum):
    """GTFS `calendar_dates.exception_type`, by its wire values."""

    ADDED = 1
    REMOVED = 2


@dataclass(frozen=True, slots=True)
class ServiceCalendar:
    """A weekly pattern bounded by a date range.

    `weekdays` is Monday-first to match `date.weekday()`, so no consumer has to
    remember an offset — GTFS's own column order is Monday-first too, and the one
    place they could diverge is here.
    """

    service_id: str
    weekdays: tuple[bool, bool, bool, bool, bool, bool, bool]
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if len(self.weekdays) != 7:
            raise ServiceError("weekdays must have exactly 7 entries, Monday first")
        if self.end_date < self.start_date:
            raise ServiceError(
                f"{self.service_id}: end_date {self.end_date} precedes start_date {self.start_date}"
            )

    def covers(self, day: date) -> bool:
        return self.start_date <= day <= self.end_date

    def pattern_runs_on(self, day: date) -> bool:
        return self.weekdays[day.weekday()]


@dataclass(frozen=True, slots=True)
class CalendarException:
    """A single date added to or removed from a service."""

    service_id: str
    day: date
    exception_type: ExceptionType


@dataclass(frozen=True, slots=True)
class ServiceSchedule:
    """One service's calendar plus every exception to it."""

    calendar: ServiceCalendar | None
    exceptions: tuple[CalendarException, ...] = ()

    def runs_on(self, day: date) -> Runs:
        """Whether the service operates. Exceptions are consulted first.

        Returning immediately on an exception is the enforcement of the precedence
        rule — there is no branch in which the weekly pattern can be reached after
        an explicit date has spoken.
        """
        for exception in self.exceptions:
            if exception.day == day:
                return Runs.YES if exception.exception_type is ExceptionType.ADDED else Runs.NO

        if self.calendar is None:
            # A service defined only by exceptions — legal GTFS, and common for
            # replacement or event services. Silence here means we hold nothing.
            return Runs.UNKNOWN

        if not self.calendar.covers(day):
            # Outside the feed's range. The feed is not asserting anything about
            # this date, and neither will we.
            return Runs.UNKNOWN

        return Runs.YES if self.calendar.pattern_runs_on(day) else Runs.NO
