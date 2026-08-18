"""Reconciliation, backfill and checkpointing — TST-DATA-002 · STEP-005.09.

WHAT THESE ARE PROTECTING
    Three ways a completeness check reports success while being wrong:

      counts match, contents do not   -> one dropped, one duplicated, reconciles exactly
      no count endpoint reads as pass -> every unverifiable provider is green forever
      a tolerance band                -> a slow leak never crosses the line in one step
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from framework.checkpoint import CheckpointError, InMemoryCheckpointStore
from reconciliation import (
    ALERT_THRESHOLD,
    BackfillRun,
    BackfillState,
    Method,
    Reconciliation,
    ReconciliationError,
    ReconciliationLog,
    SourceIndex,
    Verdict,
    digest_of,
    reconcile,
)

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


def ids(*names: str) -> list[str]:
    return list(names)


# --- what a count actually proves ------------------------------------------------


class TestACountMatchIsWeakEvidence:
    def test_one_dropped_and_one_duplicated_reconciles_perfectly_by_count(self) -> None:
        """The central limitation, demonstrated rather than described. Both sides
        hold three records and they are not the same three."""
        source = SourceIndex(provider="osm", total=3)
        result = reconcile(
            provider="osm", ingested_identities=ids("a", "b", "b"), source=source, at=NOW
        )
        assert result.verdict is Verdict.MATCHED
        assert result.detects_substitution is False

    def test_the_same_data_is_caught_when_the_source_publishes_an_index(self) -> None:
        """Same records, stronger method, opposite verdict — which is the argument
        for asking providers for an index."""
        source = SourceIndex(provider="osm", total=3, identities=("a", "b", "c"))
        result = reconcile(
            provider="osm", ingested_identities=ids("a", "b", "b"), source=source, at=NOW
        )
        assert result.verdict is Verdict.DISCREPANT
        assert result.detects_substitution is True
        assert result.missing == ("c",)

    def test_a_count_match_says_so_in_its_own_detail(self) -> None:
        """A verdict that overstates what it checked retires the suspicion that
        would have led someone to look properly."""
        result = reconcile(
            provider="osm",
            ingested_identities=ids("a", "b"),
            source=SourceIndex(provider="osm", total=2),
            at=NOW,
        )
        assert "cannot detect a substitution" in result.detail

    def test_the_digest_is_order_independent_but_not_duplicate_blind(self) -> None:
        """Sorted, so two ingestions that fetched in different orders agree.
        Duplicates kept, because a set would hide double-ingestion."""
        assert digest_of(["b", "a"]) == digest_of(["a", "b"])
        assert digest_of(["a", "a"]) != digest_of(["a"])


# --- the absence of evidence ------------------------------------------------------


class TestAnUncountableSourceIsNotReconciled:
    def test_no_index_produces_unreconciled_rather_than_matched(self) -> None:
        """The tempting answer makes every provider without a count endpoint report
        perfect completeness forever, and the dashboard is clean."""
        result = reconcile(provider="meteoswiss", ingested_identities=ids("a"), source=None, at=NOW)
        assert result.verdict is Verdict.UNRECONCILED
        assert "not evidence of completeness" in result.detail

    def test_unreconciled_is_neither_an_alert_nor_a_pass(self) -> None:
        result = reconcile(provider="meteoswiss", ingested_identities=ids(), source=None, at=NOW)
        assert result.alerts is False
        assert result.verdict is not Verdict.MATCHED

    def test_reconciling_against_another_providers_index_is_refused(self) -> None:
        with pytest.raises(ReconciliationError, match="means nothing"):
            reconcile(
                provider="osm",
                ingested_identities=ids("a"),
                source=SourceIndex(provider="opendata_swiss", total=1),
                at=NOW,
            )

    def test_a_source_that_disagrees_with_itself_is_refused(self) -> None:
        """Comparing our data against a number the source has already contradicted
        produces a verdict about nothing."""
        with pytest.raises(ReconciliationError, match="disagrees with itself"):
            SourceIndex(provider="osm", total=5, identities=("a", "b"))


# --- the threshold classifies -----------------------------------------------------


class TestDriftIsRecordedThenClassified:
    def test_a_discrepancy_below_the_threshold_is_still_recorded(self) -> None:
        """A tolerance that suppresses is how a slow leak stays invisible: every run
        green, the gap growing, nothing crossing the line in a single step."""
        result = reconcile(
            provider="osm",
            ingested_identities=ids(*[str(i) for i in range(999)]),
            source=SourceIndex(provider="osm", total=1000),
            at=NOW,
        )
        assert result.verdict is Verdict.DISCREPANT
        assert result.drift < ALERT_THRESHOLD
        assert result.alerts is False

    def test_a_discrepancy_above_the_threshold_alerts(self) -> None:
        result = reconcile(
            provider="osm",
            ingested_identities=ids(*[str(i) for i in range(900)]),
            source=SourceIndex(provider="osm", total=1000),
            at=NOW,
        )
        assert result.alerts is True

    def test_a_growing_leak_is_visible_as_a_trend(self) -> None:
        """What recording sub-threshold drift buys. No single run alerts; the series
        is unmistakable, and there is nowhere else it would have shown up."""
        log = ReconciliationLog()
        for ingested in (1000, 998, 996, 994):
            log.record(
                reconcile(
                    provider="osm",
                    ingested_identities=ids(*[str(i) for i in range(ingested)]),
                    source=SourceIndex(provider="osm", total=1000),
                    at=NOW,
                )
            )
        series = log.drift_series("osm")
        assert series == tuple(sorted(series)), "drift should be monotonically rising"
        assert log.alerting() == ()

    def test_a_seeded_shortfall_is_detected(self) -> None:
        """TST-DATA-002."""
        result = reconcile(
            provider="osm",
            ingested_identities=ids("a", "b"),
            source=SourceIndex(provider="osm", total=3, identities=("a", "b", "c")),
            at=NOW,
        )
        assert (result.verdict, result.missing, result.difference) == (
            Verdict.DISCREPANT,
            ("c",),
            -1,
        )


# --- replay safety ----------------------------------------------------------------


class TestBackfillReplay:
    def test_replaying_a_batch_applies_nothing_and_counts_the_duplicates(self) -> None:
        """TST-DATA-002. The framework's commit ordering makes re-delivery *likely*
        — a crash between handling and committing replays the batch — so this is the
        expected path rather than an edge case."""
        run = BackfillRun(InMemoryCheckpointStore(), "osm")
        assert run.apply_batch(ids("a", "b", "c"), next_cursor="p1") == 3
        assert run.apply_batch(ids("a", "b", "c"), next_cursor="p1") == 0
        progress = run.progress()
        assert (progress.applied, progress.duplicates) == (3, 3)

    def test_duplicates_are_counted_separately_from_progress(self) -> None:
        """Collapsing them would make a replayed page look like fresh progress, and
        a backfill that appears to advance while re-reading one page is exactly what
        this counter exists to expose."""
        run = BackfillRun(InMemoryCheckpointStore(), "osm")
        run.apply_batch(ids("a"), next_cursor="p1")
        run.apply_batch(ids("a"), next_cursor="p2")
        assert run.progress().applied == 1
        assert run.progress().batches == 2

    def test_the_stored_checkpoint_counts_applied_records_not_delivered_ones(self) -> None:
        """`Checkpoint.records_seen` exists, in the framework's own words, "so a
        resume that re-delivers a batch is *visible* in the numbers rather than only
        in theory".

        Counting replayed records into it destroys exactly that: three fresh records
        and three replays become the same number, and the field it was created to
        expose stops exposing anything.
        """
        store = InMemoryCheckpointStore()
        run = BackfillRun(store, "osm")
        run.apply_batch(ids("a", "b", "c"), next_cursor="p1")
        run.apply_batch(ids("a", "b", "c"), next_cursor="p2")

        stored = store.load("osm")
        assert stored is not None
        assert stored.records_seen == 3, "replayed records are not newly handled records"

    def test_a_partial_overlap_applies_only_the_new_records(self) -> None:
        run = BackfillRun(InMemoryCheckpointStore(), "osm")
        run.apply_batch(ids("a", "b"), next_cursor="p1")
        assert run.apply_batch(ids("b", "c"), next_cursor="p2") == 1
        assert run.applied_identities() == ("a", "b", "c")


class TestBackfillIsCancellableAndResumable:
    def test_cancelling_leaves_a_resumable_checkpoint(self) -> None:
        """A cancel that discarded the cursor would turn a pause into a restart from
        zero — so nobody cancels, and a runaway backfill cannot be stopped."""
        store = InMemoryCheckpointStore()
        run = BackfillRun(store, "osm")
        run.apply_batch(ids("a", "b"), next_cursor="page-2")
        progress = run.cancel()
        assert (progress.state, progress.cursor, progress.resumable) == (
            BackfillState.CANCELLED,
            "page-2",
            True,
        )

    def test_a_new_run_resumes_where_the_cancelled_one_stopped(self) -> None:
        store = InMemoryCheckpointStore()
        first = BackfillRun(store, "osm")
        first.apply_batch(ids("a", "b"), next_cursor="page-2")
        first.cancel()

        second = BackfillRun(store, "osm")
        assert second.resumed is True
        assert second.progress().cursor == "page-2"

    def test_a_cancelled_run_refuses_further_batches(self) -> None:
        run = BackfillRun(InMemoryCheckpointStore(), "osm")
        run.apply_batch(ids("a"), next_cursor="p1")
        run.cancel()
        with pytest.raises(ReconciliationError, match="not running"):
            run.apply_batch(ids("b"), next_cursor="p2")

    def test_a_completed_run_cannot_be_cancelled(self) -> None:
        run = BackfillRun(InMemoryCheckpointStore(), "osm")
        run.apply_batch(ids("a"), next_cursor="p1")
        run.complete()
        with pytest.raises(ReconciliationError, match="cannot be cancelled"):
            run.cancel()

    def test_an_empty_cursor_is_still_refused_through_this_layer(self) -> None:
        """The framework refuses it because an empty cursor means "start from the
        beginning". Asserted here so wrapping `ResumableRun` cannot quietly lose a
        guarantee it already provides."""
        run = BackfillRun(InMemoryCheckpointStore(), "osm")
        with pytest.raises(CheckpointError, match="empty cursor"):
            run.apply_batch(ids("a"), next_cursor="")


# --- evidence ---------------------------------------------------------------------


class TestResultsAreRetainedAsEvidence:
    def test_the_log_is_append_only_by_construction(self) -> None:
        """A history that can be tidied will be tidied at exactly the moment it
        becomes inconvenient."""
        surface = {n for n in dir(ReconciliationLog) if not n.startswith("_")}
        assert surface == {"record", "entries", "for_provider", "alerting", "drift_series"}
        for forbidden in ("delete", "remove", "clear", "prune", "update", "edit"):
            assert not any(forbidden in n for n in surface), forbidden

    def test_a_result_without_detail_is_refused(self) -> None:
        with pytest.raises(ReconciliationError, match="records what it compared"):
            Reconciliation(
                provider="osm",
                method=Method.COUNT,
                verdict=Verdict.MATCHED,
                ingested=1,
                source_total=1,
                at=NOW,
                detail="",
            )

    def test_a_backfill_reconciles_against_what_it_applied(self) -> None:
        """The two halves joined: replay-safe application, then a completeness check
        over the identities that survived it."""
        run = BackfillRun(InMemoryCheckpointStore(), "osm")
        run.apply_batch(ids("a", "b"), next_cursor="p1")
        run.apply_batch(ids("b", "c"), next_cursor="p2")
        run.complete()
        result = reconcile(
            provider="osm",
            ingested_identities=list(run.applied_identities()),
            source=SourceIndex(provider="osm", total=3, identities=("a", "b", "c")),
            at=NOW,
        )
        assert result.verdict is Verdict.MATCHED
        assert result.detects_substitution is True

    def test_a_negative_source_total_is_refused(self) -> None:
        with pytest.raises(ReconciliationError, match="cannot be negative"):
            SourceIndex(provider="osm", total=-1)
