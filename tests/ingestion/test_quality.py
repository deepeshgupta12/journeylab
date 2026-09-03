"""Data-quality expectations and quarantine — TST-DATA-005, TST-NFR-012 · STEP-006.08.

WHAT THESE ARE PROTECTING
    A quality gate reports "0 failures" whether it examined everything or nothing,
    and those are the same number describing very different situations:

      suite ran nothing      -> a mistyped id, a filter that matched nothing, a
                                batch nobody wrote expectations for. Reports green.
      drift with no baseline -> "stable" asserted against nothing to compare
      block treated as
      quarantine             -> a curator releases an itinerary item that points at
                                a place which does not exist
"""

from __future__ import annotations

import pathlib
import uuid
from datetime import UTC, datetime

import psycopg
import pytest
from dbcheck import DSN, requires_db
from quality import (
    CHECKS,
    DRIFT_SIGMA,
    PostgresQuarantineStore,
    QualityError,
    Quarantine,
    QuarantinedBatch,
    Result,
    Severity,
    Verdict,
    load_expectations,
    run_suite,
)

NOW = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
ORG = "dddd0000-0000-0000-0000-00000000000d"


def record(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {"id": "r-1", "source_id": "osm"}
    base.update(overrides)
    return base


# --- the failure the module is shaped around ---------------------------------------


class TestASuiteThatRanNothingIsNotAPass:
    def test_every_declared_expectation_has_an_implementation(self) -> None:
        """The YAML is the specification a curator reads. A class declared there and
        missing here means the specification and the runner disagree while the
        report says green."""
        declared = {e.id for e in load_expectations()}
        assert declared <= set(CHECKS), f"declared with no implementation: {declared - set(CHECKS)}"

    def test_an_unimplemented_expectation_raises_rather_than_skipping(
        self, tmp_path: pathlib.Path
    ) -> None:
        rogue = tmp_path / "expectations.yml"
        rogue.write_text(
            "version: 1\nexpectations:\n"
            "  - id: telepathy\n    description: knows what the provider meant\n"
            "    severity: quarantine\n"
        )
        with pytest.raises(QualityError, match="no implementation"):
            run_suite([record()], path=rogue)

    def test_the_outcome_reports_how_much_of_it_ran(self) -> None:
        """Zero failures and zero checks are the same number and very different
        facts, so the count travels with the verdict."""
        outcome = run_suite([record()])
        assert outcome.ran == outcome.expectations_declared == 6

    def test_an_empty_expectations_file_is_refused(self, tmp_path: pathlib.Path) -> None:
        empty = tmp_path / "expectations.yml"
        empty.write_text("version: 1\nexpectations: []\n")
        with pytest.raises(QualityError, match="declares no expectations"):
            run_suite([record()], path=empty)


# --- block is not quarantine ---------------------------------------------------------


class TestAHardBlockHasNoReleasePath:
    def test_an_unresolved_location_blocks_rather_than_warns(self) -> None:
        """TST-NFR-012. An item pointing at nothing produces an itinerary the
        traveller cannot follow, to a place that does not exist."""
        outcome = run_suite([record(kind="itinerary_item", resolved_place_id=None)])
        assert outcome.blocked is True
        assert outcome.admits_the_batch is False

    def test_a_curator_cannot_release_a_block(self) -> None:
        """Modelling block and quarantine as two severities loses this: the UI grows
        one release button, somebody uses it, and the hard block becomes a
        strongly-worded warning."""
        quarantine = Quarantine()
        outcome = run_suite([record(kind="itinerary_item", resolved_place_id=None)])
        quarantine.hold(outcome, organization_id=ORG, source_id="osm", count=1, at=NOW)
        with pytest.raises(QualityError, match="cannot be released"):
            quarantine.release(0, actor="curator")

    def test_a_released_block_cannot_even_be_constructed(self) -> None:
        with pytest.raises(QualityError, match="no release path"):
            QuarantinedBatch(
                organization_id=ORG,
                source_id="osm",
                expectation="referential_integrity",
                failure_detail="dangling",
                record_count=1,
                blocking=True,
                at=NOW,
                released_by="curator",
            )

    def test_a_quarantined_batch_can_be_released_once_understood(self) -> None:
        quarantine = Quarantine()
        outcome = run_suite([record(), record()])
        quarantine.hold(outcome, organization_id=ORG, source_id="osm", count=2, at=NOW)
        assert quarantine.open_items(), "a duplicate id should have been quarantined"
        released = quarantine.release(0, actor="curator")
        assert released.released_by == "curator"
        assert quarantine.open_items() == ()


# --- the absence of an answer -----------------------------------------------------------


class TestDriftWithNoBaselineIsNotAPass:
    def test_drift_reports_unavailable_rather_than_passing(self) -> None:
        """Inventing a threshold would be `BUG-026` again — a number justified by a
        belief about the world rather than by anything checkable."""
        outcome = run_suite([record()])
        drift = next(r for r in outcome.results if r.expectation_id == "distribution_drift")
        assert drift.verdict is Verdict.UNAVAILABLE
        assert "not evidence that the distribution is stable" in drift.detail

    def test_an_unavailable_check_neither_quarantines_nor_admits_on_its_own(self) -> None:
        """It has not spoken. Treating silence as approval is how a check that never
        ran becomes a check that always passes."""
        outcome = run_suite([record()])
        assert "distribution_drift" in outcome.unavailable
        drift = next(r for r in outcome.results if r.expectation_id == "distribution_drift")
        assert drift.quarantines is False
        assert drift.blocks is False

    def test_completeness_is_unavailable_when_the_source_published_no_total(self) -> None:
        """The same shape as STEP-005.09's `Unreconciled`. Fifth occurrence of this
        pattern across the codebase."""
        outcome = run_suite([record()])
        completeness = next(r for r in outcome.results if r.expectation_id == "completeness")
        assert completeness.verdict is Verdict.UNAVAILABLE


# --- the six classes -----------------------------------------------------------------------


class TestEachExpectationCatchesItsSeededViolation:
    def test_schema_catches_a_missing_required_field(self) -> None:
        outcome = run_suite([{"id": "r-1"}])
        schema = next(r for r in outcome.results if r.expectation_id == "schema")
        assert schema.verdict is Verdict.FAILED

    def test_freshness_catches_a_stale_record(self) -> None:
        outcome = run_suite([record(stale=True)])
        assert (
            next(r for r in outcome.results if r.expectation_id == "freshness").verdict
            is Verdict.FAILED
        )

    def test_completeness_catches_a_shortfall(self) -> None:
        outcome = run_suite([record(expected_count=5)])
        assert (
            next(r for r in outcome.results if r.expectation_id == "completeness").verdict
            is Verdict.FAILED
        )

    def test_uniqueness_catches_a_duplicate(self) -> None:
        outcome = run_suite([record(), record()])
        assert (
            next(r for r in outcome.results if r.expectation_id == "uniqueness").verdict
            is Verdict.FAILED
        )

    def test_a_clean_batch_is_admitted(self) -> None:
        # `value` and `baseline_stddev` are here because drift now needs something to
        # compare. Before it measured anything, this fixture passed with a baseline
        # field and no observation — precisely the vacuous pass that hid the defect.
        outcome = run_suite(
            [
                record(
                    id="a", expected_count=2, value=10.0, baseline_mean=10.0, baseline_stddev=2.0
                ),
                record(
                    id="b", expected_count=2, value=10.0, baseline_mean=10.0, baseline_stddev=2.0
                ),
            ]
        )
        assert outcome.admits_the_batch is True
        assert outcome.unavailable == ()

    def test_a_result_without_detail_is_refused(self) -> None:
        """A quarantined batch with no detail has to be re-run to learn anything,
        which is the one thing quarantine exists to avoid."""
        with pytest.raises(QualityError, match="records what it checked"):
            Result(
                expectation_id="schema",
                verdict=Verdict.FAILED,
                severity=Severity.QUARANTINE,
                detail="  ",
            )


# --- the constraints, at the database ------------------------------------------------


@pytest.mark.security
@requires_db
class TestTheQuarantineTableEnforcesItsOwnRules:
    """The Python `Quarantine` refuses these too, and that is not the same thing.

    Mutation testing dropped both constraints and every test still passed, because
    the suite exercised the class and nothing wrote to the table. A rule enforced
    only in the layer that happens to be tested is a rule any other writer bypasses
    — and the whole reason `REQ-NFR-012` is a hard block is that it must survive
    somebody reaching the row another way.
    """

    def test_a_blocking_row_cannot_be_released(self) -> None:
        org = uuid.UUID(ORG)
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'quality','Q') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            with pytest.raises(psycopg.errors.CheckViolation, match="blocking_is_not_releasable"):
                cur.execute(
                    "INSERT INTO quarantined_batches (organization_id, source_id, expectation, "
                    "failure_detail, record_count, blocking, released_at, released_by) "
                    "VALUES (%s,'osm','referential_integrity','dangling',1,true,now(),'curator')",
                    (org,),
                )

    def test_a_quarantine_row_must_carry_its_detail(self) -> None:
        org = uuid.UUID(ORG)
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'quality','Q') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            with pytest.raises(psycopg.errors.CheckViolation, match="detail_present"):
                cur.execute(
                    "INSERT INTO quarantined_batches (organization_id, source_id, expectation, "
                    "failure_detail, record_count, blocking) "
                    "VALUES (%s,'osm','schema','   ',1,false)",
                    (org,),
                )

    def test_a_release_names_who_did_it(self) -> None:
        org = uuid.UUID(ORG)
        with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'quality','Q') "
                "ON CONFLICT (id) DO NOTHING",
                (org,),
            )
            with pytest.raises(psycopg.errors.CheckViolation, match="release_is_attributed"):
                cur.execute(
                    "INSERT INTO quarantined_batches (organization_id, source_id, expectation, "
                    "failure_detail, record_count, blocking, released_at) "
                    "VALUES (%s,'osm','schema','bad',1,false,now())",
                    (org,),
                )
            cur.execute("DELETE FROM organizations WHERE id = %s", (org,))


# --- the two defects external review found ------------------------------------------


class TestDriftActuallyMeasuresDrift:
    """The first version of `_distribution_drift` returned `PASSED` whenever a
    baseline field was merely present. It measured nothing.

    Every test here had asserted the verdict for one input, and none had asserted
    that a *drifted* batch produced a different one — so the check that exists to
    notice a distribution moving could not notice a distribution moving. Found by
    external review rather than by this suite, which is the finding worth keeping.
    """

    def _batch(
        self, value: float, *, mean: float = 10.0, stddev: float = 2.0
    ) -> list[dict[str, object]]:
        return [
            {
                "id": f"r{i}",
                "source_id": "osm",
                "value": value,
                "baseline_mean": mean,
                "baseline_stddev": stddev,
            }
            for i in range(3)
        ]

    def test_a_drifted_batch_fails(self) -> None:
        drift = next(
            r
            for r in run_suite(self._batch(30.0)).results
            if r.expectation_id == "distribution_drift"
        )
        assert drift.verdict is Verdict.FAILED
        assert "10.0 sigma" in drift.detail

    def test_a_steady_batch_passes(self) -> None:
        drift = next(
            r
            for r in run_suite(self._batch(10.0)).results
            if r.expectation_id == "distribution_drift"
        )
        assert drift.verdict is Verdict.PASSED

    def test_a_shift_inside_the_threshold_passes(self) -> None:
        """Two sigma against a three-sigma threshold. The boundary is where a drift
        check earns its keep — a check that fires on any movement is one people mute."""
        drift = next(
            r
            for r in run_suite(self._batch(14.0)).results
            if r.expectation_id == "distribution_drift"
        )
        assert drift.verdict is Verdict.PASSED
        assert "2.0 sigma" in drift.detail

    def test_a_baseline_with_no_spread_cannot_judge_a_shift(self) -> None:
        """Any non-zero move is infinitely many standard deviations, which would
        quarantine every batch — unanswerable rather than failing."""
        drift = next(
            r
            for r in run_suite(self._batch(12.0, stddev=0.0)).results
            if r.expectation_id == "distribution_drift"
        )
        assert drift.verdict is Verdict.UNAVAILABLE

    def test_the_threshold_is_in_standard_deviations_not_percent(self) -> None:
        """A 10% move in price and a 10% move in duration are not comparably
        surprising, so the threshold does not have to be retuned per field."""
        assert DRIFT_SIGMA == 3.0


@pytest.mark.security
@requires_db
class TestQuarantineReachesTheTableACuratorQueries:
    """§5: "Quarantine visible to curators, not just logged."

    The in-memory `Quarantine` satisfied every test and persisted nothing — a curator
    queue that exists for the duration of one batch run is a log line with extra
    steps. Found by external review.
    """

    def test_a_held_batch_is_readable_from_the_database(self) -> None:
        org = uuid.UUID(ORG)
        with psycopg.connect(DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO organizations (id, slug, display_name) VALUES (%s,'quality','Q') "
                    "ON CONFLICT (id) DO NOTHING",
                    (org,),
                )
            quarantine = Quarantine(store=PostgresQuarantineStore(conn))
            outcome = run_suite([record(), record()])
            held = quarantine.hold(
                outcome, organization_id=str(org), source_id="osm", count=2, at=NOW
            )
            assert held, "a duplicate id should have been held"
            assert quarantine.persisted is True

            from_db = quarantine.store.open_items()  # type: ignore[union-attr]
            assert {e.expectation for e in from_db} >= {"uniqueness"}
            assert all(e.failure_detail for e in from_db)

            with conn.cursor() as cur:
                cur.execute("DELETE FROM quarantined_batches WHERE organization_id = %s", (org,))
                cur.execute("DELETE FROM organizations WHERE id = %s", (org,))

    def test_holding_without_a_store_reports_that_nothing_was_persisted(self) -> None:
        """Not an exception — a runner without a store is a legitimate test
        configuration. But the caller has to know, because the alternative is
        believing a curator can see something that reached nobody."""
        quarantine = Quarantine()
        quarantine.hold(
            run_suite([record(), record()]),
            organization_id=ORG,
            source_id="osm",
            count=2,
            at=NOW,
        )
        assert quarantine.persisted is False
