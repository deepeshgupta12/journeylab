"""Transit schedules, calendars, feed pinning and alerts — TST-DATA-002, TST-NFR-011 · STEP-005.04.

WHAT THESE PROTECT
    Each failure here produces a plan that is coherent, cited and wrong:

      25:30 rejected            the night network vanishes and reads as "no service"
      25:30 wrapped to 01:30    every late departure moves back a day (REQ-CONS-004)
      an exception ignored      a train that does not run on Christmas is in the plan
      feed drift followed       a stored stop_id resolves to a different platform
      a stop guessed            the traveller is confidently at the wrong platform
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from transit.calendar import (
    CalendarException,
    ExceptionType,
    Runs,
    ServiceCalendar,
    ServiceError,
    ServiceSchedule,
)
from transit.feed import (
    DEFAULT_ALERT_SLO,
    CoverageGap,
    FeedError,
    FeedVersion,
    ServiceAlert,
    Stop,
    StopIndex,
    TransitUnavailable,
    assert_pinned,
    transit_unavailable,
)
from transit.service_time import (
    MAX_SERVICE_HOUR,
    ServiceTime,
    ServiceTimeError,
    instant_of,
    parse_service_time,
    service_day_start,
)

ZURICH = "Europe/Zurich"


# --- a service day is not a calendar day --------------------------------------


class TestServiceTime:
    def test_a_time_past_midnight_parses_rather_than_failing(self) -> None:
        """Rejecting it deletes the night network, and the gap reads as "no
        service" rather than as a parsing failure."""
        parsed = parse_service_time("25:30")
        assert parsed.hours == 25
        assert parsed.past_midnight

    def test_it_resolves_to_the_following_calendar_day(self) -> None:
        """The other half. Wrapping to 01:30 *today* moves every late departure
        back twenty-four hours — a train that already left (REQ-CONS-004)."""
        moment = instant_of(date(2026, 8, 14), parse_service_time("25:30"), ZURICH)
        assert moment.date() == date(2026, 8, 15)
        assert (moment.hour, moment.minute) == (1, 30)

    def test_an_ordinary_time_stays_on_its_own_day(self) -> None:
        moment = instant_of(date(2026, 8, 14), parse_service_time("08:15"), ZURICH)
        assert moment.date() == date(2026, 8, 14)
        assert (moment.hour, moment.minute) == (8, 15)

    def test_seconds_are_optional(self) -> None:
        assert parse_service_time("08:15:30").seconds == 30
        assert parse_service_time("08:15").seconds == 0

    def test_an_unparseable_time_raises_rather_than_defaulting(self) -> None:
        for bad in ("", "eight", "8", "08:60", "::", "-01:00"):
            with pytest.raises(ServiceTimeError):
                parse_service_time(bad)

    def test_an_absurd_hour_is_refused(self) -> None:
        """GTFS permits large values in principle; in practice this is a feed bug,
        and accepting it schedules a departure on a day nobody planned."""
        with pytest.raises(ServiceTimeError, match="more than"):
            ServiceTime(hours=MAX_SERVICE_HOUR + 1, minutes=0)

    def test_23_59_is_not_treated_as_past_midnight(self) -> None:
        """Guards the boundary from the wrong side: if everything late counted as
        past-midnight, ordinary evening services would shift a day."""
        assert not parse_service_time("23:59").past_midnight
        assert parse_service_time("24:00").past_midnight


class TestDaylightSaving:
    """The reason service time is anchored at noon minus twelve hours."""

    def test_the_service_day_starts_at_local_midnight_on_an_ordinary_date(self) -> None:
        start = service_day_start(date(2026, 8, 14), ZURICH)
        assert (start.hour, start.minute) == (0, 0)

    def test_a_spring_forward_date_has_no_missing_midnight_problem(self) -> None:
        """Zurich springs forward on 29 March 2026. Anchoring at noon means the
        arithmetic is total on a date where 02:00-03:00 does not exist."""
        start = service_day_start(date(2026, 3, 29), ZURICH)
        assert start.date() == date(2026, 3, 29)
        # A 25:30 service on that date still lands on the 30th, not on a gap.
        moment = instant_of(date(2026, 3, 29), parse_service_time("25:30"), ZURICH)
        assert moment.date() == date(2026, 3, 30)

    def test_a_fall_back_date_is_unambiguous(self) -> None:
        """25 October 2026: 02:00-03:00 happens twice. Noon does not."""
        start = service_day_start(date(2026, 10, 25), ZURICH)
        assert start.date() == date(2026, 10, 25)
        assert start.utcoffset() is not None

    def test_the_offset_differs_across_the_boundary(self) -> None:
        """Proof the zone is doing the work rather than fixed arithmetic."""
        summer = service_day_start(date(2026, 8, 14), ZURICH)
        winter = service_day_start(date(2026, 12, 14), ZURICH)
        assert summer.utcoffset() != winter.utcoffset()


# --- exceptions beat the pattern ----------------------------------------------


def weekday_service() -> ServiceCalendar:
    return ServiceCalendar(
        service_id="WD",
        weekdays=(True, True, True, True, True, False, False),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )


class TestServiceCalendar:
    def test_the_weekly_pattern_applies(self) -> None:
        schedule = ServiceSchedule(calendar=weekday_service())
        assert schedule.runs_on(date(2026, 8, 14)) is Runs.YES  # Friday
        assert schedule.runs_on(date(2026, 8, 16)) is Runs.NO  # Sunday

    def test_a_removal_beats_the_pattern(self) -> None:
        """The asymmetric failure: ignoring a removal strands somebody at a
        station on Christmas Day."""
        schedule = ServiceSchedule(
            calendar=weekday_service(),
            exceptions=(
                CalendarException(
                    service_id="WD", day=date(2026, 12, 25), exception_type=ExceptionType.REMOVED
                ),
            ),
        )
        assert date(2026, 12, 25).weekday() == 4, "precondition: Christmas 2026 is a Friday"
        assert schedule.runs_on(date(2026, 12, 25)) is Runs.NO

    def test_an_addition_beats_the_pattern(self) -> None:
        schedule = ServiceSchedule(
            calendar=weekday_service(),
            exceptions=(
                CalendarException(
                    service_id="WD", day=date(2026, 8, 16), exception_type=ExceptionType.ADDED
                ),
            ),
        )
        assert schedule.runs_on(date(2026, 8, 16)) is Runs.YES  # a Sunday

    def test_outside_the_feed_range_is_unknown_not_no(self) -> None:
        """A feed ending on 31 December says nothing about January. Answering "does
        not run" invents a fact and produces a false infeasibility."""
        schedule = ServiceSchedule(calendar=weekday_service())
        assert schedule.runs_on(date(2027, 3, 1)) is Runs.UNKNOWN

    def test_a_service_defined_only_by_exceptions_is_unknown_elsewhere(self) -> None:
        """Legal GTFS, common for replacement services."""
        schedule = ServiceSchedule(
            calendar=None,
            exceptions=(
                CalendarException(
                    service_id="EV", day=date(2026, 8, 14), exception_type=ExceptionType.ADDED
                ),
            ),
        )
        assert schedule.runs_on(date(2026, 8, 14)) is Runs.YES
        assert schedule.runs_on(date(2026, 8, 15)) is Runs.UNKNOWN

    def test_weekdays_are_monday_first(self) -> None:
        """The one place GTFS's column order and `date.weekday()` could diverge."""
        monday_only = ServiceCalendar(
            service_id="M",
            weekdays=(True, False, False, False, False, False, False),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        schedule = ServiceSchedule(calendar=monday_only)
        assert schedule.runs_on(date(2026, 8, 10)) is Runs.YES  # Monday
        assert schedule.runs_on(date(2026, 8, 11)) is Runs.NO  # Tuesday

    def test_a_reversed_calendar_range_is_refused(self) -> None:
        with pytest.raises(ServiceError, match="precedes"):
            ServiceCalendar(
                service_id="X",
                weekdays=(True,) * 7,
                start_date=date(2026, 12, 31),
                end_date=date(2026, 1, 1),
            )


# --- TST-DATA-002: feed pinning -----------------------------------------------


def a_version(content_hash: str = "aaa111") -> FeedVersion:
    return FeedVersion(
        feed_id="ch-national",
        content_hash=content_hash,
        published_at=datetime(2026, 8, 1, tzinfo=UTC),
    )


class TestFeedPinning:
    def test_the_same_feed_passes(self) -> None:
        assert_pinned(a_version(), a_version())

    def test_changed_contents_are_rejected(self) -> None:
        """Identifiers are not stable across publications, so a stored stop_id may
        now resolve to a different platform (REQ-CONS-006)."""
        with pytest.raises(FeedError, match="feed contents changed"):
            assert_pinned(a_version("aaa111"), a_version("bbb222"))

    def test_a_different_feed_is_rejected(self) -> None:
        other = FeedVersion(
            feed_id="de-national",
            content_hash="aaa111",
            published_at=datetime(2026, 8, 1, tzinfo=UTC),
        )
        with pytest.raises(FeedError, match="expected feed"):
            assert_pinned(a_version(), other)

    def test_a_version_without_a_content_hash_is_refused(self) -> None:
        """An operator's version string is exactly what fails to catch a
        republication with the same label and different contents."""
        with pytest.raises(FeedError, match="content_hash"):
            FeedVersion(
                feed_id="ch", content_hash="  ", published_at=datetime(2026, 8, 1, tzinfo=UTC)
            )


class TestStopResolution:
    @staticmethod
    def _index() -> StopIndex:
        index = StopIndex()
        index.add(
            Stop(
                stop_id="8503000",
                name="Zürich HB",
                latitude=47.3782,
                longitude=8.5402,
                time_zone=ZURICH,
            )
        )
        return index

    def test_a_known_stop_resolves(self) -> None:
        assert self._index().resolve("8503000").name == "Zürich HB"  # type: ignore[union-attr]

    def test_an_unknown_stop_is_a_recorded_gap_not_a_guess(self) -> None:
        """No nearest-match. A confidently wrong platform is worse than an
        admitted gap, and only the gap can be disclosed."""
        index = self._index()
        assert index.resolve("does-not-exist") is None
        assert len(index.gaps) == 1
        assert index.gaps[0].kind == "unresolvable_stop"

    def test_a_stop_without_a_zone_is_refused(self) -> None:
        with pytest.raises(FeedError, match="cannot place a departure in time"):
            Stop(stop_id="x", name="X", latitude=47.0, longitude=8.0, time_zone="")

    @pytest.mark.parametrize(("lat", "lon"), [(91.0, 8.0), (47.0, 181.0), (-91.0, 8.0)])
    def test_impossible_coordinates_are_refused(self, lat: float, lon: float) -> None:
        with pytest.raises(FeedError, match="out of range"):
            Stop(stop_id="x", name="X", latitude=lat, longitude=lon, time_zone=ZURICH)


# --- TST-NFR-011: alert freshness ---------------------------------------------


def an_alert(observed_at: datetime, active_to: datetime | None = None) -> ServiceAlert:
    return ServiceAlert(
        alert_id="a1",
        headline="Line closed between Thun and Spiez",
        effect="NO_SERVICE",
        observed_at=observed_at,
        active_from=datetime(2026, 8, 14, 12, 0, tzinfo=UTC),
        active_to=active_to,
    )


class TestAlertFreshness:
    def test_a_recent_alert_is_fresh(self) -> None:
        now = datetime(2026, 8, 14, 10, 2, tzinfo=UTC)
        assert not an_alert(datetime(2026, 8, 14, 10, 0, tzinfo=UTC)).is_stale(now)

    def test_an_alert_beyond_the_slo_is_stale(self) -> None:
        now = datetime(2026, 8, 14, 10, 6, tzinfo=UTC)
        assert an_alert(datetime(2026, 8, 14, 10, 0, tzinfo=UTC)).is_stale(now)

    def test_staleness_is_about_observation_not_onset(self) -> None:
        """A closure starting tomorrow, last confirmed a week ago, is stale
        evidence about tomorrow. REQ-EVID-001 separates the two times for this."""
        alert = ServiceAlert(
            alert_id="a2",
            headline="Planned closure",
            effect="NO_SERVICE",
            observed_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
            active_from=datetime(2026, 8, 20, 0, 0, tzinfo=UTC),
            active_to=None,
        )
        assert alert.is_stale(datetime(2026, 8, 14, 9, 0, tzinfo=UTC))
        assert alert.active_at(datetime(2026, 8, 21, 9, 0, tzinfo=UTC))

    def test_the_slo_is_a_parameter_not_a_universal(self) -> None:
        """A slower provider must not silently inherit a promise this one makes."""
        alert = an_alert(datetime(2026, 8, 14, 10, 0, tzinfo=UTC))
        now = datetime(2026, 8, 14, 10, 20, tzinfo=UTC)
        assert alert.is_stale(now, slo=DEFAULT_ALERT_SLO)
        assert not alert.is_stale(now, slo=timedelta(hours=1))

    def test_an_absent_end_means_ongoing_not_ended(self) -> None:
        alert = an_alert(datetime(2026, 8, 14, 10, 0, tzinfo=UTC), active_to=None)
        assert alert.active_at(datetime(2027, 1, 1, tzinfo=UTC))

    def test_a_naive_now_is_refused(self) -> None:
        with pytest.raises(FeedError, match="timezone-aware"):
            an_alert(datetime(2026, 8, 14, 10, 0, tzinfo=UTC)).is_stale(
                datetime(2026, 8, 14, 10, 6)  # noqa: DTZ001
            )


class TestDegradation:
    def test_no_transit_is_disclosed_not_silent(self) -> None:
        gap = transit_unavailable("provider_unavailable")
        assert "walking and driving only" in gap.disclosure
        assert gap.modes_still_available == ("walking", "driving")

    def test_a_gap_without_a_disclosure_is_refused(self) -> None:
        with pytest.raises(FeedError, match="silent degradation"):
            TransitUnavailable(reason="x", disclosure="  ")

    def test_the_disclosure_says_what_is_missing_not_only_that_something_is(self) -> None:
        """A traveller needs to know which journeys are absent, not that an
        unnamed capability degraded."""
        text = transit_unavailable("provider_unavailable").disclosure.lower()
        assert "train" in text or "bus" in text


class TestCoverageGapShape:
    def test_a_gap_records_what_could_not_be_resolved(self) -> None:
        gap = CoverageGap(reference="8599999", kind="unresolvable_stop", detail="not in feed")
        assert gap.reference == "8599999"


class TestTheNoonAnchorIsSpecConformanceNotABugFix:
    """An honest record of something I could not demonstrate.

    `service_day_start` anchors at noon minus twelve hours because GTFS says so.
    The usual justification is that local midnight may not exist on a
    spring-forward date — but mutation testing replaced the anchor with a plain
    wall-clock midnight and the suite still passed, so that justification is not
    demonstrable here.

    Python's `zoneinfo` normalises a non-existent or ambiguous midnight rather than
    raising, and `noon - 12h` lands on the same instant. These tests pin that
    equivalence: the anchor stays for spec conformance, and if a future tzdata or
    Python release ever separates the two, this fails loudly instead of quietly
    changing what a departure time means.
    """

    @pytest.mark.parametrize(
        ("zone", "day"),
        [
            (ZURICH, date(2026, 3, 29)),  # spring forward
            (ZURICH, date(2026, 10, 25)),  # fall back
            (ZURICH, date(2026, 8, 14)),  # ordinary
            ("America/Havana", date(2026, 3, 8)),  # transition at midnight
            ("America/Santiago", date(2026, 9, 6)),
            ("America/Asuncion", date(2026, 10, 4)),
        ],
    )
    def test_the_two_anchors_agree_in_every_zone_tested(self, zone: str, day: date) -> None:
        from zoneinfo import ZoneInfo

        noon_anchor = service_day_start(day, zone)
        wall_clock_midnight = datetime(day.year, day.month, day.day, 0, 0, tzinfo=ZoneInfo(zone))
        assert noon_anchor.astimezone(UTC) == wall_clock_midnight.astimezone(UTC), (
            f"{zone} on {day}: the anchors diverged. If this is a real tzdata change "
            f"rather than a test error, the noon anchor has stopped being merely "
            f"spec-conformant and is now load-bearing — say so in the module docstring."
        )

    def test_a_late_service_lands_correctly_across_a_spring_forward(self) -> None:
        """Whatever the anchor, the answer must be right. 25:30 on the transition
        date is 01:30 the next day, and the hour that vanished at 02:00 does not
        move it."""
        moment = instant_of(date(2026, 3, 29), parse_service_time("25:30"), ZURICH)
        assert moment.date() == date(2026, 3, 30)
        assert (moment.hour, moment.minute) == (1, 30)
