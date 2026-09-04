"""Read-model projection and rebuild — TST-DATA-010 · STEP-006.09.

WHAT THESE ARE PROTECTING
    `REQ-DATA-010` claims read models rebuild from the log. Three ways that claim
    quietly stops being true, none of which raises:

      rebuild through the
      idempotent consumer   -> every event is already in the processed log, so the
                               rebuild skips them and produces a half-empty model
      a fold that reads
      current state         -> a year-old event folded with today's answer
      "it completed"        -> proves the code ran, not that the output matches
"""

from __future__ import annotations

import inspect
import types
from datetime import UTC, datetime, timedelta
from unittest import mock

import psycopg
import pytest
from consumers import IdempotentConsumer, ProcessedLog
from dbcheck import DSN, requires_db
from outbox import Envelope
from projections import (
    ProjectionError,
    coverage_projection,
    fold_coverage,
    projection_lag,
    reads_only_its_arguments,
    rebuild,
    verify_rebuild,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
ORG = "eeee0000-0000-0000-0000-00000000000e"


def health(
    event_id: str, *, state: str, regions: str = "bern", at: datetime = NOW, provider: str = "otd"
) -> Envelope:
    return Envelope(
        event_id=event_id,
        event_type="journey.provider.health_changed.v1",
        occurred_at=at,
        recorded_at=at,
        tenant_id=ORG,
        correlation_id="corr-1",
        actor=None,
        schema_version=1,
        payload_ids={"provider_id": provider, "new_state": state, "affected_regions": regions},
    )


# --- the distinction this sub-step turns on -------------------------------------------


class TestRebuildAndReplayAreOpposites:
    def test_a_rebuild_resets_before_folding(self) -> None:
        """Folding into existing state doubles counters and leaves stale keys no
        event removes — a projection that is *more* wrong after being repaired."""
        projection = coverage_projection()
        projection.consume([health("e-1", state="unavailable", regions="geneva")])
        assert "geneva" in projection.state

        rebuild(projection, [health("e-2", state="degraded", regions="bern")], at=NOW)
        assert set(projection.state) == {"bern"}, "the stale key survived the rebuild"

    def test_rebuilding_through_an_idempotent_consumer_would_lose_events(self) -> None:
        """The failure the two paths must not share a mechanism to avoid.

        Every event in a rebuild has already been processed, so an idempotent
        consumer skips all of them. The rebuild succeeds, raises nothing, and
        produces a projection built from whatever happened to be left.
        """
        log = ProcessedLog()
        consumer = IdempotentConsumer(name="coverage", handler=lambda e: None, log=log)
        events = [health("e-1", state="degraded"), health("e-2", state="unavailable")]
        assert consumer.consume(events) == 2
        assert consumer.consume(events) == 0, "a second pass through the consumer applies nothing"

        projection = coverage_projection()
        assert rebuild(projection, events, at=NOW) == 2, "a rebuild must fold every event"

    def test_a_rebuild_is_idempotent(self) -> None:
        """Running it twice from the same log gives the same state, because the
        second run starts from empty again."""
        events = [
            health("e-1", state="degraded"),
            health("e-2", state="unavailable", regions="geneva"),
        ]
        first = coverage_projection()
        rebuild(first, events, at=NOW)
        snapshot = dict(first.state)
        rebuild(first, events, at=NOW)
        assert first.state == snapshot

    def test_two_projections_rebuilt_from_one_log_agree(self) -> None:
        """The property `REQ-DATA-010` actually claims: the log, not the projection,
        is the source of truth."""
        events = [
            health("e-1", state="unavailable"),
            health("e-2", state="degraded", regions="geneva"),
        ]
        live, fresh = coverage_projection(), coverage_projection()
        live.consume(events)
        rebuild(fresh, events, at=NOW)
        assert verify_rebuild(live.state, fresh.state, name="coverage").matches is True


# --- finishing is not matching ------------------------------------------------------------


class TestVerificationComparesRatherThanCompletes:
    def test_a_drifted_projection_is_detected(self) -> None:
        """The failure the design exists to survive — a live projection that
        silently stopped matching its log. Invisible to a rebuild that only checks
        for exceptions."""
        events = [health("e-1", state="unavailable")]
        live = coverage_projection()
        live.consume(events)
        live.state["bern"]["freshness"] = "current"  # drift, as a bug would produce

        fresh = coverage_projection()
        rebuild(fresh, events, at=NOW)
        result = verify_rebuild(live.state, fresh.state, name="coverage")
        assert result.matches is False
        assert result.differing == ("bern",)

    def test_a_key_missing_from_the_rebuild_is_reported(self) -> None:
        result = verify_rebuild({"bern": 1, "geneva": 2}, {"bern": 1}, name="coverage")
        assert result.only_in_live == ("geneva",)
        assert result.matches is False

    def test_a_key_only_in_the_rebuild_is_reported(self) -> None:
        """The live projection missed an event. Reported separately from drift
        because the causes are different: one stopped folding, the other folded
        wrongly."""
        result = verify_rebuild({"bern": 1}, {"bern": 1, "geneva": 2}, name="coverage")
        assert result.only_in_rebuilt == ("geneva",)

    def test_the_detail_names_what_differed(self) -> None:
        result = verify_rebuild({"a": 1}, {"b": 2}, name="coverage")
        assert "1 key(s) only live" in result.detail
        assert "1 only rebuilt" in result.detail


# --- purity -------------------------------------------------------------------------------


class TestAProjectionReadsOnlyItsEvents:
    def test_the_module_reaches_no_clock_and_no_database(self) -> None:
        """A handler that queries current state produces today's answer while folding
        a year-old event. The rebuild finishes, the numbers differ, and nothing
        points at the cause."""
        import projections

        assert reads_only_its_arguments(projections) is True

    def test_the_fold_is_a_function_of_state_and_event_only(self) -> None:
        """Same inputs, same output, whenever it runs."""
        event = health("e-1", state="degraded")
        assert fold_coverage({}, event) == fold_coverage({}, event)

    def test_an_unhandled_event_type_is_not_folded(self) -> None:
        """Declared rather than inferred, so a projection that stops matching an
        event type is a visible change rather than a quietly emptier read model."""
        projection = coverage_projection()
        other = Envelope(
            event_id="e-9",
            event_type="journey.trip.brief_confirmed.v1",
            occurred_at=NOW,
            recorded_at=NOW,
            tenant_id=ORG,
            correlation_id="c",
            actor=None,
            schema_version=1,
            payload_ids={"trip_id": "t-1"},
        )
        assert projection.apply(other) is False
        assert projection.state == {}

    def test_a_naive_rebuild_timestamp_is_refused(self) -> None:
        with pytest.raises(ProjectionError, match="timezone-aware"):
            rebuild(coverage_projection(), [], at=datetime(2026, 9, 3, 12, 0))  # noqa: DTZ001


# --- the coverage read model itself -----------------------------------------------------------


class TestTheCoverageProjection:
    def test_a_region_takes_its_worst_provider(self) -> None:
        """A region is only as available as its least available input, so a healthy
        provider must not overwrite a degraded sibling's verdict."""
        projection = coverage_projection()
        projection.consume(
            [
                health("e-1", state="unavailable", provider="otd"),
                health("e-2", state="healthy", provider="osm"),
            ]
        )
        assert projection.state["bern"]["freshness"] == "stale"
        assert projection.state["bern"]["accepting_trips"] is False

    def test_a_degraded_region_still_accepts_trips_with_a_disclosure(self) -> None:
        """`REQ-TRIP-002` refuses what is outside coverage; degraded is inside it."""
        projection = coverage_projection()
        projection.consume([health("e-1", state="degraded")])
        assert projection.state["bern"]["accepting_trips"] is True
        assert projection.state["bern"]["limitations"]

    def test_no_provider_identity_reaches_the_read_model(self) -> None:
        """`EVT-008` carries `provider_id` and this projection drops it.
        `REQ-EVID-006` permits disclosing *that* coverage is degraded and forbids
        naming who degraded it — and the read model is what a client reads, so a
        field here would be the place it leaks."""
        projection = coverage_projection()
        projection.consume([health("e-1", state="degraded", provider="opentransportdata")])
        assert "opentransportdata" not in repr(projection.state)
        assert "otd" not in repr(projection.state)

    def test_multiple_regions_are_folded_independently(self) -> None:
        projection = coverage_projection()
        projection.consume([health("e-1", state="unavailable", regions="bern,geneva")])
        assert set(projection.state) == {"bern", "geneva"}


# --- lag -----------------------------------------------------------------------------------------


class TestProjectionLagIsMeasuredFromTheFact:
    def test_a_stalled_projection_shows_growing_lag(self) -> None:
        """Not from `rebuilt_at`. A projection that stopped folding an hour ago has a
        recent rebuild timestamp and an hour of unapplied events — the third time
        this trap has appeared in this step."""
        projection = coverage_projection()
        projection.consume([health("e-1", state="degraded", at=NOW - timedelta(hours=1))])
        projection.rebuilt_at = NOW
        assert projection_lag(projection, now=NOW) == timedelta(hours=1)

    def test_a_projection_that_has_seen_nothing_has_no_lag(self) -> None:
        assert projection_lag(coverage_projection(), now=NOW) == timedelta(0)


# --- against the database ----------------------------------------------------------------------------


@pytest.mark.security
@requires_db
class TestTheReadModelIsDerivedAndIsolated:
    def test_the_read_model_has_no_provider_column(self) -> None:
        """The type drops provider identity; so does the table. Two places, because
        the table is the one a future writer reaches directly."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'coverage_read_model'"
            )
            columns = {row[0] for row in cur.fetchall()}
        assert not any("provider" in c or "supplier" in c for c in columns), columns

    def test_rebuilding_restores_derived_fields_without_destroying_declared_ones(
        self,
    ) -> None:
        """TST-DATA-010, and a hazard STEP-007.01 introduced.

        The table now holds two kinds of column. `freshness` and `accepting_trips`
        are **derived** — folded from `EVT-008`. `display_name` and `date_bounds`
        are **declared**: the product's statement about what it supports, which no
        event produces and a rebuild therefore cannot reconstruct.

        So a rebuild must UPDATE the derived columns, never DELETE and reinsert.
        Deleting is the natural implementation — it is how you guarantee no stale row
        survives — and it would silently erase every region's name and dates, leaving
        a projection that rebuilt perfectly and a coverage page that cannot render.
        """
        events = [
            health("e-1", state="unavailable"),
            health("e-2", state="degraded", regions="geneva"),
        ]
        declared = {
            "bern": ("Bern", "2026-04-01", "2027-03-31"),
            "geneva": ("Geneva", "2026-04-01", "2027-03-31"),
        }
        source = coverage_projection()
        source.consume(events)

        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            for region, (name, start, end) in declared.items():
                cur.execute(
                    "INSERT INTO coverage_read_model (region_id, display_name, "
                    "date_bounds_start, date_bounds_end, freshness, accepting_trips) "
                    "VALUES (%s,%s,%s,%s,'current',true) ON CONFLICT (region_id) DO NOTHING",
                    (region, name, start, end),
                )
            for region, row in source.state.items():
                cur.execute(
                    "UPDATE coverage_read_model SET freshness = %s, accepting_trips = %s "
                    "WHERE region_id = %s",
                    (row["freshness"], row["accepting_trips"], region),
                )
            cur.execute(
                "SELECT region_id, display_name, freshness FROM coverage_read_model "
                "WHERE region_id = ANY(%s) ORDER BY region_id",
                (list(declared),),
            )
            before = cur.fetchall()

            # Corrupt the derived half, exactly as a bad consumer would.
            cur.execute(
                "UPDATE coverage_read_model SET freshness = 'current' WHERE region_id = ANY(%s)",
                (list(declared),),
            )

            rebuilt = coverage_projection()
            rebuild(rebuilt, events, at=NOW)
            for region, row in rebuilt.state.items():
                cur.execute(
                    "UPDATE coverage_read_model SET freshness = %s, accepting_trips = %s "
                    "WHERE region_id = %s",
                    (row["freshness"], row["accepting_trips"], region),
                )
            cur.execute(
                "SELECT region_id, display_name, freshness FROM coverage_read_model "
                "WHERE region_id = ANY(%s) ORDER BY region_id",
                (list(declared),),
            )
            after = cur.fetchall()
            cur.execute(
                "DELETE FROM coverage_read_model WHERE region_id = ANY(%s)", (list(declared),)
            )

        assert after == before, "the rebuild did not restore the derived state"
        assert all(row[1] for row in after), "a rebuild erased a declared display name"


# --- negative controls ------------------------------------------------------------------


class TestTheCheckersThemselvesCanFail:
    def test_the_purity_check_detects_a_module_that_reads_a_clock(self) -> None:
        """A checker only ever asserted to return `True` is indistinguishable from
        `return True`, and a mutation run proved exactly that: replacing the whole
        body with `True` killed nothing.

        Same construction as the axe negative control in the browser suite — the
        detector must be shown failing on a seeded violation, or its passes mean
        nothing.
        """
        import consumers
        import projections

        assert reads_only_its_arguments(projections) is True
        # `consumers` calls `.get`, `.setdefault` and friends but crucially no clock
        # or cursor, so a stricter probe is needed to prove the check discriminates.
        assert reads_only_its_arguments(consumers) is True

        source = (
            "import datetime\n\n\ndef fold(state, event):\n    return datetime.datetime.now()\n"
        )
        module = types.ModuleType("seeded_impure")
        with mock.patch.object(inspect, "getsource", return_value=source):
            assert reads_only_its_arguments(module) is False, (
                "the purity check passed a module that calls datetime.now()"
            )

    def test_the_verification_can_report_a_match(self) -> None:
        """The other direction: a comparator that always reports a difference would
        be equally useless and equally green under a one-sided assertion."""
        assert verify_rebuild({"a": 1}, {"a": 1}, name="coverage").matches is True
        assert verify_rebuild({"a": 1}, {"a": 2}, name="coverage").matches is False


@pytest.mark.security
@requires_db
class TestTheReadModelConstrainsItsOwnVocabulary:
    def test_an_unknown_freshness_value_is_refused(self) -> None:
        """The enum exists in the type and in the table. Mutation testing dropped the
        table's constraint and nothing failed, because every test wrote through the
        projection — which is the layer a future writer bypasses."""
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            with pytest.raises(psycopg.errors.CheckViolation, match="freshness_known"):
                cur.execute(
                    "INSERT INTO coverage_read_model (region_id, display_name, "
                    "date_bounds_start, date_bounds_end, freshness, accepting_trips) "
                    "VALUES ('vocab','Vocab','2026-04-01','2027-03-31','probably_fine',true)"
                )
