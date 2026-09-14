"""Writing a folded projection to its table — TST-EVID-006 · STEP-007.05.

WHAT THESE ARE PROTECTING
    The write that did not exist until this sub-step, and the four ways it goes
    wrong quietly:

      delete-and-reinsert  -> erases declared columns no event can restore, and
                              the rebuild reports success
      insert-on-miss       -> publishes a region the product never declared,
                              with no name, no dates and no zone
      report-every-row     -> a "changed" signal that is always true, so the cache
                              it exists to bust is busted on every poll
      report-no-row        -> a change that never reaches the traveller, which is
                              the disclosure failure REQ-EVID-006 is about

    The first is the dangerous one. It is the natural implementation — deleting is
    how you guarantee no stale row survives — and its damage is invisible to every
    assertion about the derived columns, which are exactly the columns it gets
    right.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import psycopg
import pytest
from dbcheck import DSN, requires_db
from outbox import Envelope
from projections import coverage_projection, rebuild
from read_models import (
    DECLARED_COVERAGE_COLUMNS,
    DERIVED_COVERAGE_COLUMNS,
    ReadModelError,
    apply_coverage_state,
)

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
ORG = "eeee0000-0000-0000-0000-00000000000e"


def health(event_id: str, *, state: str, regions: str) -> Envelope:
    return Envelope(
        event_id=event_id,
        event_type="journey.provider.health_changed.v1",
        occurred_at=NOW,
        recorded_at=NOW,
        tenant_id=ORG,
        correlation_id="corr-1",
        actor=None,
        schema_version=1,
        payload_ids={"provider_id": "otd", "new_state": state, "affected_regions": regions},
    )


class FakeCursor:
    """Records statements. Returns a row for every UPDATE, so "changed" is the
    default and a test asserting "not changed" has to earn it."""

    def __init__(self, *, returns: bool = True) -> None:
        self.statements: list[str] = []
        self.params: list[tuple[object, ...]] = []
        self._returns = returns

    def execute(self, query: str, params: tuple[object, ...] = (), /) -> object:
        self.statements.append(query)
        self.params.append(params)
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [("bern",)] if self._returns else []


# --- the rule that used to live only in a test --------------------------------


class TestItOnlyEverUpdates:
    def test_no_statement_deletes_or_inserts(self) -> None:
        """The declared columns are unrecoverable, so the write must not be able to
        remove them even in principle — asserted on the SQL, not on the outcome.

        An outcome assertion would pass against a DELETE followed by an INSERT that
        happened to restore the right values in the test's fixture.
        """
        cursor = FakeCursor()
        apply_coverage_state(cursor, {"bern": {"freshness": "degraded", "accepting_trips": True}})
        for statement in cursor.statements:
            upper = statement.upper()
            assert "DELETE" not in upper, statement
            assert "INSERT" not in upper, statement
            assert "UPDATE" in upper

    def test_it_touches_only_the_derived_columns(self) -> None:
        cursor = FakeCursor()
        apply_coverage_state(cursor, {"bern": {"freshness": "stale", "accepting_trips": False}})
        written = " ".join(cursor.statements)
        for column in DERIVED_COVERAGE_COLUMNS:
            assert column in written, column
        for column in DECLARED_COVERAGE_COLUMNS:
            assert column not in written, f"{column} is declared and must never be written here"

    def test_a_row_without_freshness_is_refused_rather_than_written(self) -> None:
        """A fold that changed shape would otherwise put a NULL where a public enum
        is read, and the page would render an empty status."""
        with pytest.raises(ReadModelError):
            apply_coverage_state(FakeCursor(), {"bern": {"accepting_trips": True}})

    def test_accepting_trips_is_derived_when_absent_rather_than_defaulted_to_true(self) -> None:
        """`stale` means not accepting. A default of True would publish a region as
        bookable precisely when its sources are gone."""
        cursor = FakeCursor()
        apply_coverage_state(cursor, {"bern": {"freshness": "stale"}})
        assert cursor.params[0][1] is False


# --- against the real schema --------------------------------------------------


@requires_db
class TestAgainstTheRealTable:
    """`RISK-017`: the graph holds one node per `.sql` file, so the blast radius of
    a schema rule comes from running it."""

    def _declare(self, cur: Any, region_id: str, name: str) -> None:
        cur.execute(
            "INSERT INTO coverage_read_model (region_id, display_name, date_bounds_start, "
            "date_bounds_end, time_zone, freshness, accepting_trips) "
            "VALUES (%s,%s,'2026-04-01','2027-03-31','Europe/Zurich','current',true) "
            "ON CONFLICT (region_id) DO NOTHING",
            (region_id, name),
        )

    def test_the_declared_half_survives_a_write(self) -> None:
        """The failure that would look like success: derived columns correct,
        display name gone, coverage page unable to render."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            self._declare(cur, "rm-bern", "Bern")
            try:
                apply_coverage_state(
                    cur,
                    {
                        "rm-bern": {
                            "freshness": "degraded",
                            "accepting_trips": True,
                            "limitations": ["rm-bern is running on degraded sources"],
                        }
                    },
                )
                cur.execute(
                    "SELECT display_name, date_bounds_start, time_zone, freshness, limitations "
                    "FROM coverage_read_model WHERE region_id = 'rm-bern'"
                )
                row = cur.fetchall()[0]
            finally:
                cur.execute("DELETE FROM coverage_read_model WHERE region_id = 'rm-bern'")

        assert row[0] == "Bern", "the declared name was destroyed by a derived write"
        assert row[1] is not None, "the declared dates were destroyed"
        assert row[2] == "Europe/Zurich", "the declared zone was destroyed"
        assert row[3] == "degraded"
        assert row[4] == ["rm-bern is running on degraded sources"]

    def test_an_undeclared_region_is_dropped_rather_than_invented(self) -> None:
        """Health for a region nobody declared has nowhere to go. Inserting one
        would publish a region with no name, no dates and no zone."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            changed = apply_coverage_state(
                cur, {"rm-never-declared": {"freshness": "stale", "accepting_trips": False}}
            )
            cur.execute(
                "SELECT count(*) FROM coverage_read_model WHERE region_id = 'rm-never-declared'"
            )
            count = cur.fetchall()[0][0]

        assert changed == frozenset()
        assert count == 0, "a region was invented from an event"

    def test_only_regions_that_actually_changed_are_reported(self) -> None:
        """The return value drives cache invalidation. A writer that reported every
        row would bust the cache on every poll and teach the caller to ignore it."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            self._declare(cur, "rm-geneva", "Geneva")
            try:
                state = {
                    "rm-geneva": {
                        "freshness": "degraded",
                        "accepting_trips": True,
                        "limitations": ["thin"],
                    }
                }
                first = apply_coverage_state(cur, state)
                second = apply_coverage_state(cur, state)
            finally:
                cur.execute("DELETE FROM coverage_read_model WHERE region_id = 'rm-geneva'")

        assert first == frozenset({"rm-geneva"}), "the first write reported no change"
        assert second == frozenset(), "an unchanged write reported a change"

    def test_a_rebuild_round_trips_through_the_table(self) -> None:
        """STEP-006.09's property, now exercised through production code rather
        than through SQL written inside a test."""
        events = [
            health("rm-e1", state="unavailable", regions="rm-bern"),
            health("rm-e2", state="degraded", regions="rm-geneva"),
        ]
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            self._declare(cur, "rm-bern", "Bern")
            self._declare(cur, "rm-geneva", "Geneva")
            try:
                live = coverage_projection()
                live.consume(events)
                apply_coverage_state(cur, live.state)

                # Corrupt the derived half, exactly as a bad consumer would.
                cur.execute(
                    "UPDATE coverage_read_model SET freshness = 'current' "
                    "WHERE region_id IN ('rm-bern','rm-geneva')"
                )

                rebuilt = coverage_projection()
                rebuild(rebuilt, events, at=NOW)
                apply_coverage_state(cur, rebuilt.state)

                cur.execute(
                    "SELECT region_id, display_name, freshness FROM coverage_read_model "
                    "WHERE region_id IN ('rm-bern','rm-geneva') ORDER BY region_id"
                )
                rows = cur.fetchall()
            finally:
                cur.execute(
                    "DELETE FROM coverage_read_model WHERE region_id IN ('rm-bern','rm-geneva')"
                )

        assert rows == [("rm-bern", "Bern", "stale"), ("rm-geneva", "Geneva", "degraded")]


# --- REQ-EVID-006: no supplier identity reaches the table ---------------------


class TestNoProviderIdentityIsWritten:
    def test_the_fold_drops_provider_id_before_it_can_be_persisted(self) -> None:
        """`EVT-008` carries `provider_id`. Two layers drop it — the fold and the
        table — and this asserts the first, because the second is a schema check
        that would pass against a fold quietly carrying it in memory."""
        projection = coverage_projection()
        projection.consume([health("rm-e3", state="degraded", regions="rm-bern")])
        rendered = repr(projection.state)
        for forbidden in ("otd", "provider_id", "provider"):
            assert forbidden not in rendered, forbidden

    def test_no_statement_this_module_issues_mentions_a_provider(self) -> None:
        cursor = FakeCursor()
        apply_coverage_state(cursor, {"bern": {"freshness": "degraded", "accepting_trips": True}})
        written = " ".join(cursor.statements).lower()
        for forbidden in ("provider", "supplier", "quota"):
            assert forbidden not in written, forbidden
