"""The three time axes and DST-safe arithmetic — TST-DATA-007 · STEP-006.02.

WHAT THESE ARE PROTECTING
    `DATA_ARCHITECTURE` §3 calls confusing "when we learned it" with "when it is
    true" the most common source of wrong travel plans. Both are timestamps on the
    same row, both compile, and both return plausible rows.

    And one class below exists because the module's own first draft had the bug:
    subtracting two aware datetimes that share a `tzinfo` gives the WALL CLOCK
    difference, so every duration across a DST boundary was wrong by an hour.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg
import pytest
from dbcheck import DSN, requires_db
from domain.temporal import (
    AxisFilter,
    TemporalError,
    effective_during,
    elapsed_between,
    is_dst_transition_day,
    local_calendar_days,
    observed_since,
    recorded_since,
    same_local_time_next_day,
)
from hypothesis import given, settings
from hypothesis import strategies as st

ZURICH = "Europe/Zurich"
Z = ZoneInfo(ZURICH)

#: Europe/Zurich, 2026. Spring forward loses an hour, autumn back gains one.
SPRING_FORWARD = datetime(2026, 3, 29, 12, 0, tzinfo=Z)
AUTUMN_BACK = datetime(2026, 10, 25, 12, 0, tzinfo=Z)

pytestmark = pytest.mark.property


# --- the bug this module was written to prevent, found in this module -------------


class TestElapsedTimeSurvivesADstBoundary:
    def test_the_day_the_clocks_go_forward_is_twenty_three_hours(self) -> None:
        """Nine to nine across spring-forward is 23 elapsed hours.

        The first draft of `elapsed_between` was `return end - start`. Python
        documents that two aware datetimes sharing a `tzinfo` subtract as wall
        clock, so it returned 24 — with both offsets perfectly correct, which is
        what makes it invisible. Wrong by an hour, in the direction that makes a
        tight itinerary look feasible.
        """
        start = datetime(2026, 3, 28, 9, 0, tzinfo=Z)
        assert elapsed_between(start, same_local_time_next_day(start, zone=ZURICH)) == timedelta(
            hours=23
        )

    def test_the_day_the_clocks_go_back_is_twenty_five_hours(self) -> None:
        start = datetime(2026, 10, 24, 9, 0, tzinfo=Z)
        assert elapsed_between(start, same_local_time_next_day(start, zone=ZURICH)) == timedelta(
            hours=25
        )

    def test_the_traveller_still_reads_nine_oclock(self) -> None:
        """The other half. Elapsed time changes; the wall clock does not, because
        "same time tomorrow" is a calendar question and a person means the clock."""
        for start in (
            datetime(2026, 3, 28, 9, 0, tzinfo=Z),
            datetime(2026, 10, 24, 9, 0, tzinfo=Z),
        ):
            assert same_local_time_next_day(start, zone=ZURICH).hour == 9

    def test_the_trap_is_in_subtraction_not_addition(self) -> None:
        """The asymmetry, pinned — because my first version of this test asserted
        the opposite and was wrong.

        With `zoneinfo`, `aware + timedelta` is **wall-clock** arithmetic, so
        adding a day already preserves 09:00. Subtracting two aware datetimes that
        share a `tzinfo` is **also** wall-clock, which is where the bug lives:
        it reports 24 hours for a 23-hour day. Only conversion to UTC gives elapsed
        time, in either direction.

        `same_local_time_next_day` therefore exists to name the intent and to
        refuse naive input, not because `+` is broken. Recorded here so nobody
        "simplifies" it away believing it was redundant — the equivalence is a
        property of `zoneinfo`, and `pytz` does not share it.
        """
        start = datetime(2026, 3, 28, 9, 0, tzinfo=Z)
        assert (start + timedelta(days=1)).hour == 9, "addition is wall clock"
        assert same_local_time_next_day(start, zone=ZURICH).hour == 9

        naive_subtraction = (start + timedelta(days=1)) - start
        assert naive_subtraction == timedelta(hours=24), "subtraction is ALSO wall clock"
        assert elapsed_between(start, start + timedelta(days=1)) == timedelta(hours=23)

    def test_a_transition_day_is_recognised(self) -> None:
        assert is_dst_transition_day(SPRING_FORWARD, zone=ZURICH) is True
        assert is_dst_transition_day(AUTUMN_BACK, zone=ZURICH) is True
        assert is_dst_transition_day(datetime(2026, 3, 15, 12, 0, tzinfo=Z), zone=ZURICH) is False

    @settings(max_examples=200, deadline=None)
    @given(
        offset_hours=st.integers(min_value=-72, max_value=72),
        duration_hours=st.integers(min_value=0, max_value=96),
    )
    def test_elapsed_time_never_disagrees_with_utc(
        self, offset_hours: int, duration_hours: int
    ) -> None:
        """The property, over windows straddling both 2026 transitions.

        Elapsed time is defined by UTC. Whatever the local clock does, the answer
        must equal the UTC difference — which is the invariant the wall-clock bug
        broke.
        """
        base = SPRING_FORWARD + timedelta(hours=offset_hours)
        end = base + timedelta(hours=duration_hours)
        assert elapsed_between(base, end) == (end.astimezone(UTC) - base.astimezone(UTC))

    @settings(max_examples=100, deadline=None)
    @given(days=st.integers(min_value=1, max_value=400))
    def test_same_local_time_always_preserves_the_wall_clock(self, days: int) -> None:
        """Over more than a year, so both transitions are crossed in both directions."""
        start = datetime(2026, 1, 15, 14, 30, tzinfo=Z)
        moved = same_local_time_next_day(start, zone=ZURICH, days=days)
        assert (moved.hour, moved.minute) == (14, 30)


class TestCalendarDaysAreNotElapsedDays:
    def test_a_two_hour_overnight_stay_is_one_night(self) -> None:
        """Dividing elapsed time by 24 says zero. Hotel nights, day passes and "how
        many days is this trip" are all calendar questions."""
        start = datetime(2026, 6, 1, 23, 0, tzinfo=Z)
        end = datetime(2026, 6, 2, 1, 0, tzinfo=Z)
        assert local_calendar_days(start, end, zone=ZURICH) == 1
        assert elapsed_between(start, end) == timedelta(hours=2)

    def test_counting_is_done_in_the_local_zone_not_utc(self) -> None:
        """23:30 local in summer is 21:30 UTC — the UTC date is still the day
        before, so counting in UTC drops a night."""
        start = datetime(2026, 6, 1, 23, 30, tzinfo=Z)
        end = datetime(2026, 6, 2, 23, 30, tzinfo=Z)
        assert local_calendar_days(start, end, zone=ZURICH) == 1


# --- the two axes -------------------------------------------------------------------


class TestAxisChoiceIsExplicit:
    def test_each_helper_names_the_axis_it_filters_on(self) -> None:
        now = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
        assert effective_during(now, now + timedelta(days=3)).axis == "effective"
        assert observed_since(now).axis == "observed"
        assert recorded_since(now).axis == "recorded"

    def test_there_is_no_general_purpose_time_filter_to_reach_for(self) -> None:
        """The structural half.

        A `filter_by_time(column, ...)` helper would make the axis a parameter, and
        a parameter is exactly what gets passed wrongly. Each question has its own
        function so choosing the wrong one means typing the wrong word.
        """
        import domain.temporal as temporal

        public = {n for n in dir(temporal) if not n.startswith("_")}
        for forbidden in ("filter_by_time", "time_filter", "between", "any_axis"):
            assert forbidden not in public, forbidden

    def test_an_open_ended_window_is_still_effective(self) -> None:
        """`temporal-validity.json`: absent is not expired."""
        now = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
        assert "effective_to IS NULL" in effective_during(now, now).sql

    def test_a_backwards_window_is_refused(self) -> None:
        now = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
        with pytest.raises(TemporalError, match="cannot end before"):
            effective_during(now, now - timedelta(days=1))

    @pytest.mark.parametrize(
        "call",
        [
            lambda m: effective_during(m, m),
            observed_since,
            recorded_since,
            lambda m: same_local_time_next_day(m, zone=ZURICH),
            lambda m: elapsed_between(m, m),
        ],
    )
    def test_a_naive_datetime_is_refused_everywhere(self, call: object) -> None:
        """Not "UTC by default" — a value whose meaning was lost before it arrived."""
        naive = datetime(2026, 8, 19, 12, 0)  # noqa: DTZ001
        with pytest.raises(TemporalError, match="naive"):
            call(naive)  # type: ignore[operator]

    def test_an_unknown_zone_is_refused(self) -> None:
        with pytest.raises(TemporalError, match="unknown IANA zone"):
            same_local_time_next_day(datetime(2026, 8, 19, 12, 0, tzinfo=UTC), zone="Mars/Olympus")


# --- against the database -------------------------------------------------------------


@pytest.mark.security
@requires_db
class TestTheDatabaseAgreesWithTheHelpers:
    def test_a_fresh_fact_outside_the_trip_window_is_excluded(self) -> None:
        """The headline defect: a fact observed sixty seconds ago about last summer
        is fresh and inapplicable. The effective filter excludes it; an observed
        filter would return it."""
        org = "88888888-8888-8888-8888-888888888888"
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'temporal','T') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            cur.execute(
                """INSERT INTO evidence_facts
                   (organization_id, field_class, value, source_id, licence_id,
                    confidence, access_label, observed_at, effective_from, effective_to)
                   VALUES (%s,'hours','{}','osm','ODbL-1.0',0.9,'public',
                           now(), now() - interval '400 days', now() - interval '300 days')""",
                (org,),
            )
            trip_start = datetime(2026, 8, 19, tzinfo=UTC)
            axis = effective_during(trip_start, trip_start + timedelta(days=3))
            cur.execute(
                f"SELECT count(*) FROM evidence_facts WHERE organization_id = %s AND {axis.sql}",  # noqa: S608
                (org, *axis.params),
            )
            row = cur.fetchone()
            assert row is not None and row[0] == 0, "a stale-window fact must not be planned on"

            observed = observed_since(trip_start - timedelta(days=1))
            cur.execute(
                f"SELECT count(*) FROM evidence_facts WHERE organization_id = %s AND {observed.sql}",  # noqa: S608
                (org, *observed.params),
            )
            row = cur.fetchone()
            assert row is not None and row[0] == 1, "the same fact IS recently observed"
            cur.execute("DELETE FROM organizations WHERE id = %s", (org,))

    def test_one_source_may_not_contradict_itself_over_the_same_window(self) -> None:
        org = "99999999-9999-9999-9999-999999999999"
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'overlap','O') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            insert = """INSERT INTO evidence_facts
                   (organization_id, place_id, field_class, value, source_id, licence_id,
                    confidence, access_label, observed_at, effective_from, effective_to)
                   VALUES (%s, NULL, 'hours', %s, %s, 'ODbL-1.0', 0.9, 'public',
                           now(), '2026-06-01Z', '2026-09-01Z')"""
            # place_id is NULL here on purpose: an exclusion constraint keyed on a
            # nullable column never conflicts, because NULL = NULL is unknown. The
            # first version of the constraint had exactly that hole, and region-level
            # facts escaped it silently. It is coalesced now, and this is the test
            # that found it.
            cur.execute(insert, (org, '{"v":1}', "osm"))
            with pytest.raises(psycopg.errors.ExclusionViolation):
                cur.execute(insert, (org, '{"v":2}', "osm"))
            cur.execute("DELETE FROM organizations WHERE id = %s", (org,))

    def test_two_sources_may_disagree_and_both_are_kept(self) -> None:
        """REQ-EVID-002, and the reason the exclusion key includes `source_id`.

        Keying it by place and field alone — the obvious rule — would make the
        schema reject the second source's fact, enforcing a requirement violation
        with an error that reads like a data bug.
        """
        org = "aaaa9999-9999-9999-9999-999999999999"
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'conflict','C') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            insert = """INSERT INTO evidence_facts
                   (organization_id, place_id, field_class, value, source_id, licence_id,
                    confidence, access_label, observed_at, effective_from, effective_to)
                   VALUES (%s, NULL, 'hours', %s, %s, 'ODbL-1.0', 0.9, 'public',
                           now(), '2026-06-01Z', '2026-09-01Z')"""
            cur.execute(insert, (org, '{"v":1}', "osm"))
            cur.execute(insert, (org, '{"v":2}', "opendata_swiss"))
            cur.execute("SELECT count(*) FROM evidence_facts WHERE organization_id = %s", (org,))
            row = cur.fetchone()
            assert row is not None and row[0] == 2, "conflicting evidence stays visible"
            cur.execute("DELETE FROM organizations WHERE id = %s", (org,))


def test_the_axis_filter_carries_its_sql_and_params_together() -> None:
    """A fragment separated from its parameters is how the wrong values get bound."""
    now = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
    built = effective_during(now, now + timedelta(days=1))
    assert isinstance(built, AxisFilter)
    assert built.sql.count("%s") == len(built.params)
    assert len(inspect.signature(effective_during).parameters) == 2
