"""The browser suite's seeding tool — BUG-038, `BR-067` §6.

WHAT THIS IS PROTECTING
    The Playwright suite now seeds a reserved region before it runs and removes it,
    with any waitlist rows its run created, afterwards. If `remove` stopped removing
    (mutant 9), every browser run would leave a region and an email-bearing row in
    whatever database it was pointed at — personal data with no owner, which is the
    exact shape `STEP-007.04` §8 forbids. These tests hold the tool to both halves of
    the contract, against a real database, through the platform's own consent rule for
    the row that matters.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, date, datetime

import e2e_region
import psycopg
import pytest
from dbcheck import DSN, requires_db
from platform_api.waitlist import join_waitlist

MARKER = f"{e2e_region.WAITLIST_MARKER}pytest"


def _region_row(cur: psycopg.Cursor) -> tuple[object, ...] | None:
    cur.execute(
        "SELECT freshness, accepting_trips, date_bounds_start, date_bounds_end "
        "FROM coverage_read_model WHERE region_id = %s",
        (e2e_region.REGION_ID,),
    )
    return cur.fetchone()


def _marker_rows(cur: psycopg.Cursor) -> int:
    cur.execute(
        "SELECT count(*) FROM waitlist_entries WHERE region_query LIKE %s",
        (f"{e2e_region.WAITLIST_MARKER}%",),
    )
    row = cur.fetchone()
    assert row is not None
    return int(row[0])


def _join_with_marker(cur: psycopg.Cursor) -> None:
    """A real waitlist row, through the real rule — not a hand-built INSERT that
    could drift from the schema the way a fixture would."""
    join_waitlist(
        cur,
        email="e2e-pytest@example.invalid",
        region_query=MARKER,
        purpose="waitlist_notification",
        granted=True,
        now=datetime.now(UTC),
    )


@pytest.fixture
def cur() -> Iterator[psycopg.Cursor]:
    with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cursor:
        try:
            yield cursor
        finally:
            # Whatever a test did, leave nothing behind — including on failure.
            e2e_region.remove(cursor)


@requires_db
class TestSeed:
    def test_declares_the_region_with_a_window_around_today(self, cur: psycopg.Cursor) -> None:
        summary = e2e_region.seed(cur)
        row = _region_row(cur)
        assert row is not None
        freshness, accepting, start, end = row
        # The driver returns `object`; the schema says `date`. Assert the second, do not cast.
        assert isinstance(start, date) and isinstance(end, date)
        today = datetime.now(UTC).date()
        assert (freshness, accepting) == ("current", True)
        assert start < today < end, "the window must contain today, or dated tests rot"
        assert summary["region_id"] == e2e_region.REGION_ID

    def test_is_idempotent_and_resets_a_crashed_runs_state(self, cur: psycopg.Cursor) -> None:
        e2e_region.seed(cur)
        cur.execute(
            "UPDATE coverage_read_model SET freshness = 'stale', accepting_trips = false "
            "WHERE region_id = %s",
            (e2e_region.REGION_ID,),
        )
        e2e_region.seed(cur)
        row = _region_row(cur)
        assert row is not None and row[:2] == ("current", True)
        cur.execute(
            "SELECT count(*) FROM coverage_read_model WHERE region_id = %s",
            (e2e_region.REGION_ID,),
        )
        assert cur.fetchone() == (1,)

    def test_removes_and_counts_leftover_marker_rows(self, cur: psycopg.Cursor) -> None:
        # A run that crashed before teardown leaves its rows. Setup removes them AND
        # reports the count, so a missing teardown is visible rather than absorbed.
        e2e_region.seed(cur)
        _join_with_marker(cur)
        assert _marker_rows(cur) == 1
        summary = e2e_region.seed(cur)
        assert summary["leftover_waitlist_rows_removed"] == 1
        assert _marker_rows(cur) == 0


@requires_db
class TestRemove:
    def test_deletes_the_region_and_the_runs_waitlist_rows(self, cur: psycopg.Cursor) -> None:
        e2e_region.seed(cur)
        _join_with_marker(cur)
        assert _region_row(cur) is not None
        assert _marker_rows(cur) == 1

        summary = e2e_region.remove(cur)

        assert _region_row(cur) is None, "mutant 9: the region survived teardown"
        assert _marker_rows(cur) == 0, "mutant 9: an email-bearing row survived teardown"
        assert summary["region_rows_removed"] == 1
        assert summary["waitlist_rows_removed"] == 1

    def test_touches_nothing_else(self, cur: psycopg.Cursor) -> None:
        # Another region and a non-marker waitlist row must be untouched by a sweep
        # that is scoped to the suite's own reservations.
        cur.execute(
            "INSERT INTO coverage_read_model (region_id, display_name, date_bounds_start, "
            "date_bounds_end, time_zone, freshness, accepting_trips) "
            "VALUES ('pytest-other', 'Other', '2026-01-01', '2030-12-31', 'Europe/Zurich', "
            "'current', true) ON CONFLICT (region_id) DO NOTHING"
        )
        try:
            e2e_region.seed(cur)
            e2e_region.remove(cur)
            cur.execute("SELECT count(*) FROM coverage_read_model WHERE region_id = 'pytest-other'")
            assert cur.fetchone() == (1,)
        finally:
            cur.execute("DELETE FROM coverage_read_model WHERE region_id = 'pytest-other'")


class TestTheDsnIsRequired:
    def test_no_default_and_a_message_naming_where_the_default_lives(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("JOURNEYLAB_DATABASE_URL", raising=False)
        with pytest.raises(SystemExit) as exc:
            e2e_region.dsn()
        assert "apps/web/src/test/dsn.ts" in str(exc.value)

    def test_blank_is_the_same_as_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOURNEYLAB_DATABASE_URL", "   ")
        with pytest.raises(SystemExit):
            e2e_region.dsn()
        assert os.environ["JOURNEYLAB_DATABASE_URL"] == "   "
