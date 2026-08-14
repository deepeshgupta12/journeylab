"""Places, hours and accessibility — TST-DATA-001, TST-DATA-005 · STEP-005.02.

WHAT THESE ARE REALLY PROTECTING
    Not "does it parse". The failures that matter here produce a **confident wrong
    itinerary**, and each has a defined severity in this repository:

      unknown hours read as CLOSED -> a feasible plan reported infeasible
                                      (REQ-CONS-005)
      unknown hours read as OPEN   -> a plan built on a shut place
                                      (REQ-CONS-004, S1 by definition)
      inferred accessibility       -> REQ-PRIV-003, a sensitive attribute we made up
      hours without a zone         -> wrong by an hour, twice a year
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest
from places.adapter import AdapterError, adapt
from places.hours import (
    Availability,
    HoursError,
    Interval,
    SeasonalHours,
    availability_at,
    availability_in_season,
    parse,
    split_at_midnight,
    unknown_hours,
)
from places.licence import (
    KNOWN_LICENCES,
    OPENDATA_SWISS,
    OPENSTREETMAP,
    LicenceError,
    LicenceRecord,
    ShareAlike,
    attribution_for,
)

ZURICH = ZoneInfo("Europe/Zurich")


def at(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=ZURICH)


# --- TST-DATA-001: no licence, no ingestion -----------------------------------


class TestLicenceGate:
    def test_ingestion_requires_a_licence_by_signature(self) -> None:
        """REQ-DATA-001 says "before ingestion is enabled". A sequencing claim is
        kept by structure or not at all — there is no call that omits it."""
        with pytest.raises(TypeError):
            adapt({"name": "x", "time_zone": "Europe/Zurich"})  # type: ignore[call-arg]

    def test_a_non_commercial_licence_cannot_be_recorded_at_all(self) -> None:
        """Open-Meteo's free tier is the live example (ADR-016 §2): CC-BY data,
        non-commercial terms. Recording it as usable invites exactly that mistake."""
        with pytest.raises(LicenceError, match="commercial use is not permitted"):
            LicenceRecord(
                licence_id="open-meteo-free",
                source_name="Open-Meteo",
                terms_url="https://open-meteo.com/en/license",
                attribution_required=True,
                attribution_text="Open-Meteo",
                max_cache_seconds=None,
                share_alike=ShareAlike.NONE,
                commercial_use_permitted=False,
            )

    def test_attribution_required_without_text_is_refused(self) -> None:
        """An obligation nobody can render is an obligation nobody meets."""
        with pytest.raises(LicenceError, match="attribution"):
            LicenceRecord(
                licence_id="x",
                source_name="X",
                terms_url="https://example.test/terms",
                attribution_required=True,
                attribution_text="   ",
                max_cache_seconds=None,
                share_alike=ShareAlike.NONE,
                commercial_use_permitted=True,
            )

    def test_terms_must_be_re_readable(self) -> None:
        with pytest.raises(LicenceError, match="terms_url"):
            LicenceRecord(
                licence_id="x",
                source_name="X",
                terms_url="somewhere in an email",
                attribution_required=False,
                attribution_text="",
                max_cache_seconds=None,
                share_alike=ShareAlike.NONE,
                commercial_use_permitted=True,
            )

    def test_osm_is_recorded_as_share_alike(self) -> None:
        """ADR-016 §1: the evidence pack is a derivative database on the plain
        reading of ODbL, and a posture is owed before STEP-010. This is the field
        that decision will act on, so it must be right from the first ingestion."""
        assert OPENSTREETMAP.share_alike is ShareAlike.DERIVATIVE_DATABASE
        assert OPENDATA_SWISS.share_alike is ShareAlike.NONE

    def test_share_alike_is_three_valued(self) -> None:
        """ "We have not read the terms" and "the terms impose nothing" are
        different facts. A boolean loses the first one."""
        assert {s.value for s in ShareAlike} == {"none", "derivative_database", "unknown"}

    def test_attribution_is_stable_and_deduplicated(self) -> None:
        assert attribution_for({"ODbL-1.0", "opendata.swiss"}) == [
            "Source: opendata.swiss",
            "© OpenStreetMap contributors",
        ]

    def test_every_known_licence_permits_commercial_use(self) -> None:
        """The constraint the owner set is open data with zero spend — which is not
        the same as 'any open licence'. This asserts the register honours it."""
        assert all(rec.commercial_use_permitted for rec in KNOWN_LICENCES.values())


# --- the distinction the solver depends on ------------------------------------


class TestUnknownIsNotClosed:
    """The single most important behaviour in this module.

    Collapsing unknown into either neighbour breaks the solver in opposite
    directions, and both are failures this product exists to prevent.
    """

    def test_absent_hours_are_unknown_not_closed(self) -> None:
        hours = unknown_hours("Europe/Zurich")
        assert availability_at(hours, at(2026, 8, 12, 12)) is Availability.UNKNOWN

    def test_parsed_hours_outside_a_span_are_closed_not_unknown(self) -> None:
        """The converse. If everything were UNKNOWN the distinction would be
        useless, and a solver could never rule anything out."""
        hours = parse("Mo-Fr 09:00-17:00", time_zone="Europe/Zurich")
        assert availability_at(hours, at(2026, 8, 16, 12)) is Availability.CLOSED

    def test_the_three_states_are_distinct(self) -> None:
        hours = parse("Mo-Fr 09:00-17:00", time_zone="Europe/Zurich")
        assert availability_at(hours, at(2026, 8, 12, 12)) is Availability.OPEN
        assert availability_at(hours, at(2026, 8, 16, 12)) is Availability.CLOSED
        assert availability_at(unknown_hours("Europe/Zurich"), at(2026, 8, 12, 12)) is (
            Availability.UNKNOWN
        )

    def test_an_unparseable_rule_becomes_unknown_never_a_guess(self) -> None:
        """The parser covers a deliberate subset. Guessing at `Mo-Fr 09:00-17:00;
        PH off` would produce confidently wrong hours, and wrong hours are a
        hard-constraint violation rather than a display bug."""
        with pytest.raises(HoursError, match="unsupported"):
            parse("Mo-Fr sunrise-sunset", time_zone="Europe/Zurich")


# --- TST-DATA-005: midnight, DST and seasons ----------------------------------


class TestMidnight:
    def test_a_span_crossing_midnight_is_split(self) -> None:
        """Stored naively it has start > end and every comparison downstream
        silently reverses."""
        hours = parse("Fr 22:00-02:00", time_zone="Europe/Zurich")
        assert len(hours.intervals) == 2
        assert {i.day for i in hours.intervals} == {4, 5}

    def test_every_interval_satisfies_start_before_end(self) -> None:
        """The invariant the split exists to preserve, asserted directly."""
        hours = parse("Fr 22:00-02:00; Sa 23:00-01:00", time_zone="Europe/Zurich")
        assert all(i.start < i.end for i in hours.intervals)

    def test_an_interval_that_would_reverse_is_refused(self) -> None:
        with pytest.raises(HoursError, match="start < end"):
            Interval(day=0, start=time(22, 0), end=time(2, 0))

    def test_open_after_midnight_on_the_following_day(self) -> None:
        hours = parse("Fr 22:00-02:00", time_zone="Europe/Zurich")
        # Saturday 00:30 — inside the second half of Friday's span.
        assert availability_at(hours, at(2026, 8, 15, 0, 30)) is Availability.OPEN
        # Saturday 03:00 — after it.
        assert availability_at(hours, at(2026, 8, 15, 3, 0)) is Availability.CLOSED

    def test_a_zero_length_span_is_refused(self) -> None:
        with pytest.raises(HoursError, match="zero-length"):
            split_at_midnight(0, time(9, 0), time(9, 0))

    def test_24_00_means_end_of_day_not_hour_zero(self) -> None:
        hours = parse("Mo 09:00-24:00", time_zone="Europe/Zurich")
        assert len(hours.intervals) == 1
        assert availability_at(hours, at(2026, 8, 10, 23, 30)) is Availability.OPEN


class TestTimeZones:
    def test_a_naive_moment_is_refused(self) -> None:
        """Assuming local is how a plan becomes wrong by an hour twice a year."""
        hours = parse("Mo-Fr 09:00-17:00", time_zone="Europe/Zurich")
        with pytest.raises(HoursError, match="timezone-aware"):
            availability_at(hours, datetime(2026, 8, 12, 12, 0))  # noqa: DTZ001

    def test_a_bogus_zone_is_refused_at_parse_time(self) -> None:
        """`ZoneInfo` raises its own error type; the point is that a bad zone is
        rejected where it is written rather than stored and failing at use."""
        from zoneinfo import ZoneInfoNotFoundError

        with pytest.raises(ZoneInfoNotFoundError):
            parse("Mo-Fr 09:00-17:00", time_zone="Europe/Atlantis")

    def test_hours_are_evaluated_in_the_places_zone_not_the_callers(self) -> None:
        """A traveller in New York asking about a Zurich museum at 08:00 UTC.

        In Zurich that is 10:00 and the museum is open. Evaluated in the caller's
        zone it would read as closed — the exact class of error a required
        `time_zone` exists to prevent.
        """
        hours = parse("Mo-Fr 09:00-17:00", time_zone="Europe/Zurich")
        moment = datetime(2026, 8, 12, 8, 0, tzinfo=UTC)
        assert availability_at(hours, moment) is Availability.OPEN

    def test_dst_boundary_is_handled_by_the_zone_not_by_arithmetic(self) -> None:
        """Zurich moves to CET on 25 October 2026. 10:00 local is open on both
        sides, and the UTC offset differs — which is precisely why the comparison
        happens after `astimezone` rather than on stored offsets."""
        hours = parse("Mo-Su 09:00-17:00", time_zone="Europe/Zurich")
        before = datetime(2026, 10, 24, 10, 0, tzinfo=ZURICH)
        after = datetime(2026, 10, 26, 10, 0, tzinfo=ZURICH)
        assert before.utcoffset() != after.utcoffset()
        assert availability_at(hours, before) is Availability.OPEN
        assert availability_at(hours, after) is Availability.OPEN


class TestSeasons:
    """TST-DATA-005: seasonal hours produce correct effective windows."""

    @staticmethod
    def _summer() -> SeasonalHours:
        return SeasonalHours(
            hours=parse("Mo-Su 09:00-17:00", time_zone="Europe/Zurich"),
            effective_from=date(2026, 5, 1),
            effective_to=date(2026, 10, 31),
        )

    def test_inside_the_window_it_applies(self) -> None:
        assert (
            availability_in_season((self._summer(),), at(2026, 7, 1, 12), time_zone="Europe/Zurich")
            is Availability.OPEN
        )

    def test_outside_every_window_is_unknown_not_closed(self) -> None:
        """A railway with summer hours and no winter entry tells us nothing about
        January. Reporting CLOSED would invent a fact the source never stated."""
        assert (
            availability_in_season(
                (self._summer(),), at(2026, 1, 15, 12), time_zone="Europe/Zurich"
            )
            is Availability.UNKNOWN
        )

    def test_an_absent_end_is_open_ended_not_expired(self) -> None:
        """The same distinction `temporal-validity.json` makes, for the same reason."""
        season = SeasonalHours(
            hours=parse("Mo-Su 09:00-17:00", time_zone="Europe/Zurich"),
            effective_from=date(2026, 5, 1),
            effective_to=None,
        )
        assert season.applies_on(date(2030, 1, 1))

    def test_a_reversed_window_is_refused(self) -> None:
        with pytest.raises(HoursError, match="precedes"):
            SeasonalHours(
                hours=unknown_hours("Europe/Zurich"),
                effective_from=date(2026, 10, 1),
                effective_to=date(2026, 5, 1),
            )

    def test_unknown_beats_closed_when_seasons_overlap(self) -> None:
        """Claiming closed on the strength of one season while another is silent
        would again be inventing a fact."""
        known = SeasonalHours(
            hours=parse("Mo-Su 09:00-10:00", time_zone="Europe/Zurich"),
            effective_from=date(2026, 1, 1),
            effective_to=None,
        )
        silent = SeasonalHours(
            hours=unknown_hours("Europe/Zurich"),
            effective_from=date(2026, 1, 1),
            effective_to=None,
        )
        assert (
            availability_in_season((known, silent), at(2026, 7, 1, 15), time_zone="Europe/Zurich")
            is Availability.UNKNOWN
        )


# --- REQ-PRIV-003: declared, never inferred -----------------------------------


class TestAccessibility:
    def test_declared_features_are_kept(self) -> None:
        place = adapt(
            {
                "name": "Kunsthaus",
                "time_zone": "Europe/Zurich",
                "accessibility": ["wheelchair", "step_free"],
            },
            licence=OPENSTREETMAP,
        )
        assert place.accessibility == ("step_free", "wheelchair")

    def test_an_unknown_key_is_dropped_not_mapped_to_a_neighbour(self) -> None:
        """A wrong accessibility fact is worse for the person relying on it than a
        missing one, so nothing is guessed at."""
        place = adapt(
            {
                "name": "Kunsthaus",
                "time_zone": "Europe/Zurich",
                "accessibility": ["wheelchair", "probably_fine"],
            },
            licence=OPENSTREETMAP,
        )
        assert place.accessibility == ("wheelchair",)
        assert any("not in the declared vocabulary" in w for w in place.warnings)

    def test_absent_accessibility_is_empty_and_that_means_not_declared(self) -> None:
        """Empty is "the source is silent", NOT "this place is inaccessible"
        (REQ-PRIV-003). The warning list is where the difference is visible."""
        place = adapt({"name": "Kunsthaus", "time_zone": "Europe/Zurich"}, licence=OPENSTREETMAP)
        assert place.accessibility == ()


# --- adapter behaviour --------------------------------------------------------


class TestAdapter:
    def test_provenance_carries_the_licence(self) -> None:
        """`Provenance.licence_id` was added in STEP-004.06 and had no user until
        now. ADR-016 makes it load-bearing: ODbL and non-ODbL facts will sit side
        by side in one pack from the first ingestion."""
        place = adapt({"name": "Kunsthaus", "time_zone": "Europe/Zurich"}, licence=OPENSTREETMAP)
        assert place.provenance.licence_id == "ODbL-1.0"
        assert place.provenance.observed_at.tzinfo is not None

    def test_a_place_without_a_time_zone_is_refused(self) -> None:
        with pytest.raises(AdapterError, match="time_zone is required"):
            adapt({"name": "Kunsthaus"}, licence=OPENSTREETMAP)

    def test_a_place_without_a_name_is_refused(self) -> None:
        with pytest.raises(AdapterError, match="cannot be rendered or cited"):
            adapt({"time_zone": "Europe/Zurich"}, licence=OPENSTREETMAP)

    def test_unparseable_hours_do_not_discard_the_whole_place(self) -> None:
        """The name and location remain usable facts. Only the hours are unknown,
        and saying so is more useful than dropping the record."""
        place = adapt(
            {
                "name": "Kunsthaus",
                "time_zone": "Europe/Zurich",
                "opening_hours": "whenever the curator feels like it",
            },
            licence=OPENSTREETMAP,
        )
        assert place.name == "Kunsthaus"
        assert place.hours.unknown
        assert any("UNKNOWN" in w for w in place.warnings)

    def test_naive_observed_at_is_refused(self) -> None:
        with pytest.raises(AdapterError, match="timezone-aware"):
            adapt(
                {"name": "K", "time_zone": "Europe/Zurich"},
                licence=OPENSTREETMAP,
                observed_at=datetime(2026, 8, 12, 12),  # noqa: DTZ001
            )

    def test_confidence_outside_zero_to_one_is_refused(self) -> None:
        with pytest.raises(AdapterError, match="confidence"):
            adapt(
                {"name": "K", "time_zone": "Europe/Zurich"},
                licence=OPENSTREETMAP,
                confidence=1.5,
            )
