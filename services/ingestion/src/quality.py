"""Data-quality expectations and quarantine — STEP-006.08 (REQ-DATA-005, REQ-NFR-012).

A SUITE THAT RAN NOTHING MUST NOT REPORT A PASS

    This is the failure mode the module is shaped around. An expectation runner
    naturally reports "0 failures" for a batch it never examined — a mistyped class
    name, a filter that matched nothing, a batch of a kind nobody wrote expectations
    for — and "0 failures" is indistinguishable from "everything is fine".

    So `run_suite` counts what it *ran*, requires every class declared in
    `domain_expectations.yml` to have an implementation, and treats a non-empty
    batch that produced zero results as a failure of the suite rather than a
    property of the data.

BLOCK AND QUARANTINE ARE DIFFERENT AFFORDANCES, NOT DIFFERENT SEVERITIES

    `REQ-NFR-012` makes an unresolved location a **hard block**. A quarantined batch
    can be inspected and released by a curator once the cause is understood; a
    blocked one cannot, because releasing it would put an itinerary item pointing at
    nothing into planning.

    Modelling both as "severity: high" and "severity: critical" loses that: the UI
    grows one release button, somebody uses it, and the hard block becomes a
    strongly-worded warning. The database refuses to release a blocking row.

DRIFT WITH NO BASELINE IS NOT A PASSING DRIFT CHECK

    Distribution drift needs a previous distribution, and no provider corpus has
    been fetched. Inventing a threshold here would be `BUG-026` again — a number
    justified by a belief about the world.

    `DriftUnavailable` is the honest value, and it is the fifth time this shape has
    been needed: `ProfileUnsupported`, `TransitUnavailable`, `ObjectiveWithdrawn`,
    `Unreconciled`, and now this. At five occurrences it is the house pattern for
    "we could not answer this", carried where it can be seen rather than rounded to
    the nearest verdict.
"""

from __future__ import annotations

import enum
import pathlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

import yaml

EXPECTATIONS_FILE = (
    pathlib.Path(__file__).resolve().parents[3] / "data" / "quality" / "domain_expectations.yml"
)


class QualityError(ValueError):
    """A quality run was refused. No batch was admitted on a partial result."""


class Severity(enum.StrEnum):
    #: Inspectable and releasable by a curator once the cause is understood.
    QUARANTINE = "quarantine"
    #: No release path. `REQ-NFR-012`.
    BLOCK = "block"


class Verdict(enum.StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    #: The check could not run — no baseline, no comparison, no answer. Not a pass.
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class Expectation:
    """One declared expectation, read from the YAML rather than defined in code."""

    id: str
    description: str
    severity: Severity


@dataclass(frozen=True, slots=True)
class Result:
    expectation_id: str
    verdict: Verdict
    severity: Severity
    detail: str

    def __post_init__(self) -> None:
        if not self.detail.strip():
            raise QualityError(
                f"{self.expectation_id}: a result records what it checked and what it "
                f"found. Without it, a quarantined batch has to be re-run to learn "
                f"anything, which is the one thing quarantine exists to avoid"
            )

    @property
    def quarantines(self) -> bool:
        return self.verdict is Verdict.FAILED and self.severity is Severity.QUARANTINE

    @property
    def blocks(self) -> bool:
        return self.verdict is Verdict.FAILED and self.severity is Severity.BLOCK


def load_expectations(path: pathlib.Path | None = None) -> tuple[Expectation, ...]:
    """Read the declared expectations. The file is the specification."""
    source = path or EXPECTATIONS_FILE
    document = yaml.safe_load(source.read_text())
    declared = document.get("expectations") or []
    if not declared:
        raise QualityError(f"{source} declares no expectations")
    return tuple(
        Expectation(
            id=str(entry["id"]),
            description=str(entry["description"]),
            severity=Severity(entry["severity"]),
        )
        for entry in declared
    )


#: An expectation declared in the YAML with no implementation here is a **failure**.
#: Skipping it would mean the specification and the runner disagree while the suite
#: reports green — the specification being the thing a curator reads.
Check = Callable[[Sequence[dict[str, Any]]], Result]


def _schema(batch: Sequence[dict[str, Any]]) -> Result:
    missing = [r for r in batch if not {"id", "source_id"} <= set(r)]
    return Result(
        expectation_id="schema",
        verdict=Verdict.FAILED if missing else Verdict.PASSED,
        severity=Severity.QUARANTINE,
        detail=f"{len(missing)} of {len(batch)} record(s) missing required fields",
    )


def _freshness(batch: Sequence[dict[str, Any]]) -> Result:
    stale = [r for r in batch if r.get("stale") is True]
    return Result(
        expectation_id="freshness",
        verdict=Verdict.FAILED if stale else Verdict.PASSED,
        severity=Severity.QUARANTINE,
        detail=f"{len(stale)} of {len(batch)} record(s) past their field-class threshold",
    )


def _completeness(batch: Sequence[dict[str, Any]]) -> Result:
    expected = {r.get("expected_count") for r in batch if r.get("expected_count") is not None}
    if not expected:
        return Result(
            expectation_id="completeness",
            verdict=Verdict.UNAVAILABLE,
            severity=Severity.QUARANTINE,
            detail="the source published no total, so completeness was not checked",
        )
    target = max(int(v) for v in expected if v is not None)
    return Result(
        expectation_id="completeness",
        verdict=Verdict.FAILED if len(batch) < target else Verdict.PASSED,
        severity=Severity.QUARANTINE,
        detail=f"{len(batch)} ingested against {target} claimed at the source",
    )


def _uniqueness(batch: Sequence[dict[str, Any]]) -> Result:
    identities = [r.get("id") for r in batch]
    duplicates = len(identities) - len(set(identities))
    return Result(
        expectation_id="uniqueness",
        verdict=Verdict.FAILED if duplicates else Verdict.PASSED,
        severity=Severity.QUARANTINE,
        detail=f"{duplicates} duplicate provider identit(ies) in {len(batch)} record(s)",
    )


def _referential_integrity(batch: Sequence[dict[str, Any]]) -> Result:
    """`REQ-NFR-012`: every itinerary item references a resolved location.

    A block rather than a quarantine. An item pointing at nothing produces an
    itinerary the traveller cannot follow to a place that does not exist, and no
    curator inspection makes that safe to release.
    """
    dangling = [
        r for r in batch if r.get("kind") == "itinerary_item" and not r.get("resolved_place_id")
    ]
    return Result(
        expectation_id="referential_integrity",
        verdict=Verdict.FAILED if dangling else Verdict.PASSED,
        severity=Severity.BLOCK,
        detail=f"{len(dangling)} itinerary item(s) reference an unresolved location",
    )


#: How far the batch mean may move from the recorded baseline before the batch is
#: held, as a multiple of the baseline's own standard deviation. Provisional pending
#: `DEC-005`; expressed in standard deviations rather than as a percentage so it
#: does not have to be retuned per field — a 10% move in price and a 10% move in
#: duration are not comparably surprising.
DRIFT_SIGMA = 3.0


def _distribution_drift(batch: Sequence[dict[str, Any]]) -> Result:
    """Compare the batch mean against the recorded baseline, or report that it could
    not be compared.

    THE FIRST VERSION OF THIS FUNCTION DID NOT MEASURE ANYTHING. It returned
    `PASSED` whenever a baseline field was merely present — the exact vacuous pass
    this module's docstring is about, written into the one check whose whole job is
    noticing a distribution moving. Found by external review, not by these tests,
    because every test asserted the verdict and none asserted that a drifted batch
    produced a different one.
    """
    observed = [
        float(r["value"])
        for r in batch
        if isinstance(r.get("value"), (int, float)) and not isinstance(r.get("value"), bool)
    ]
    baselines = [
        (float(r["baseline_mean"]), float(r.get("baseline_stddev") or 0.0))
        for r in batch
        if r.get("baseline_mean") is not None
    ]
    if not baselines or not observed:
        return Result(
            expectation_id="distribution_drift",
            verdict=Verdict.UNAVAILABLE,
            severity=Severity.QUARANTINE,
            detail=(
                "no recorded baseline to compare against, so drift was not evaluated. "
                "This is the absence of a comparison, not evidence that the "
                "distribution is stable"
            ),
        )

    baseline_mean, baseline_stddev = baselines[0]
    batch_mean = sum(observed) / len(observed)
    shift = abs(batch_mean - baseline_mean)

    if baseline_stddev <= 0:
        # A baseline with no spread cannot say whether a shift is surprising. Any
        # non-zero move is infinitely many standard deviations, which would quarantine
        # every batch — so this is unanswerable rather than failing.
        return Result(
            expectation_id="distribution_drift",
            verdict=Verdict.UNAVAILABLE if shift else Verdict.PASSED,
            severity=Severity.QUARANTINE,
            detail=(
                f"baseline mean {baseline_mean:g} has no recorded spread, so a shift of "
                f"{shift:g} cannot be judged surprising or ordinary"
            ),
        )

    sigmas = shift / baseline_stddev
    drifted = sigmas > DRIFT_SIGMA
    return Result(
        expectation_id="distribution_drift",
        verdict=Verdict.FAILED if drifted else Verdict.PASSED,
        severity=Severity.QUARANTINE,
        detail=(
            f"batch mean {batch_mean:g} against baseline {baseline_mean:g} — "
            f"{sigmas:.1f} sigma, threshold {DRIFT_SIGMA:g} sigma"
        ),
    )


CHECKS: dict[str, Check] = {
    "schema": _schema,
    "freshness": _freshness,
    "completeness": _completeness,
    "uniqueness": _uniqueness,
    "referential_integrity": _referential_integrity,
    "distribution_drift": _distribution_drift,
}


@dataclass(frozen=True, slots=True)
class SuiteOutcome:
    """What the suite did, including how much of it ran."""

    results: tuple[Result, ...]
    expectations_declared: int

    @property
    def ran(self) -> int:
        return len(self.results)

    @property
    def blocked(self) -> bool:
        return any(r.blocks for r in self.results)

    @property
    def quarantined(self) -> bool:
        return any(r.quarantines for r in self.results)

    @property
    def unavailable(self) -> tuple[str, ...]:
        return tuple(r.expectation_id for r in self.results if r.verdict is Verdict.UNAVAILABLE)

    @property
    def admits_the_batch(self) -> bool:
        """Whether planning may use this data. Unavailable checks do not admit it on
        their own — they simply have not spoken."""
        return not self.blocked and not self.quarantined


def run_suite(batch: Sequence[dict[str, Any]], *, path: pathlib.Path | None = None) -> SuiteOutcome:
    """Run every declared expectation, or refuse.

    Two refusals, and both exist because the alternative is a green suite that
    checked nothing:

      * an expectation declared in the YAML with no implementation — the
        specification a curator reads and the code that runs would disagree while
        the report says pass;
      * a non-empty batch that produced no results at all.
    """
    expectations = load_expectations(path)
    unimplemented = [e.id for e in expectations if e.id not in CHECKS]
    if unimplemented:
        raise QualityError(
            f"declared with no implementation: {', '.join(unimplemented)}. A suite that "
            f"skips them reports green while the specification and the runner disagree"
        )

    results = tuple(CHECKS[e.id](batch) for e in expectations)
    if batch and not results:
        raise QualityError(
            "a non-empty batch produced no expectation results. Zero failures and zero "
            "checks are the same number and very different facts"
        )
    return SuiteOutcome(results=results, expectations_declared=len(expectations))


@dataclass(frozen=True, slots=True)
class QuarantinedBatch:
    organization_id: str
    source_id: str
    expectation: str
    failure_detail: str
    record_count: int
    blocking: bool
    at: datetime
    released_by: str | None = None

    def __post_init__(self) -> None:
        if self.blocking and self.released_by is not None:
            raise QualityError(
                f"{self.expectation} is a hard block (REQ-NFR-012) and has no release "
                f"path. A releasable block is a strongly-worded warning"
            )


class QuarantineStore(Protocol):
    """Persistence for held batches, behind a port.

    A port because `DEC-007` has not chosen a platform, and an in-memory
    implementation would otherwise be the only one — which is what "visible to
    curators" cannot mean. `PostgresQuarantineStore` below is the real one and the
    table is `quarantined_batches`.
    """

    def add(self, entry: QuarantinedBatch) -> None: ...
    def open_items(self) -> tuple[QuarantinedBatch, ...]: ...
    def mark_released(self, entry: QuarantinedBatch, *, actor: str) -> None: ...


class PostgresQuarantineStore:
    """The store a curator can actually query.

    Added after external review pointed out that the in-memory quarantine was never
    wired to the table §5 requires — "visible to curators, not just logged" is not
    satisfied by an object that exists for the duration of one batch run.
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def add(self, entry: QuarantinedBatch) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                "INSERT INTO quarantined_batches (organization_id, source_id, expectation, "
                "failure_detail, record_count, blocking, quarantined_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    entry.organization_id,
                    entry.source_id,
                    entry.expectation,
                    entry.failure_detail,
                    entry.record_count,
                    entry.blocking,
                    entry.at,
                ),
            )

    def open_items(self) -> tuple[QuarantinedBatch, ...]:
        with self._connection.cursor() as cur:
            cur.execute(
                "SELECT organization_id, source_id, expectation, failure_detail, "
                "record_count, blocking, quarantined_at, released_by "
                "FROM quarantined_batches WHERE released_at IS NULL "
                "ORDER BY quarantined_at, expectation"
            )
            return tuple(
                QuarantinedBatch(
                    organization_id=str(row[0]),
                    source_id=row[1],
                    expectation=row[2],
                    failure_detail=row[3],
                    record_count=row[4],
                    blocking=row[5],
                    at=row[6],
                    released_by=row[7],
                )
                for row in cur.fetchall()
            )

    def mark_released(self, entry: QuarantinedBatch, *, actor: str) -> None:
        """The database refuses a blocking release too, and that is deliberate
        duplication: this is the layer a second writer would bypass."""
        with self._connection.cursor() as cur:
            cur.execute(
                "UPDATE quarantined_batches SET released_at = now(), released_by = %s "
                "WHERE organization_id = %s AND expectation = %s AND released_at IS NULL",
                (actor, entry.organization_id, entry.expectation),
            )


@dataclass
class Quarantine:
    """Failed batches, listable by a curator rather than buried in a log.

    `store` is optional so the rules can be tested without a database, but a run
    that holds a batch with no store has held nothing anybody can act on — which is
    why `hold` says so rather than silently keeping the list to itself.
    """

    store: QuarantineStore | None = None
    #: False once a batch has been held with no store behind it.
    persisted: bool = True
    _entries: list[QuarantinedBatch] = field(default_factory=list)

    def hold(
        self,
        outcome: SuiteOutcome,
        *,
        organization_id: str,
        source_id: str,
        count: int,
        at: datetime,
    ) -> tuple[QuarantinedBatch, ...]:
        held = tuple(
            QuarantinedBatch(
                organization_id=organization_id,
                source_id=source_id,
                expectation=result.expectation_id,
                failure_detail=result.detail,
                record_count=count,
                blocking=result.blocks,
                at=at,
            )
            for result in outcome.results
            if result.quarantines or result.blocks
        )
        self._entries.extend(held)
        if self.store is not None:
            for entry in held:
                self.store.add(entry)
        elif held:
            # Not an exception: a batch runner without a store is a legitimate test
            # configuration. But the caller has to know that nothing was persisted,
            # because a curator queue that only exists in memory is a log line with
            # extra steps.
            self.persisted = False
        return held

    def open_items(self) -> tuple[QuarantinedBatch, ...]:
        return tuple(e for e in self._entries if e.released_by is None)

    def release(self, index: int, *, actor: str) -> QuarantinedBatch:
        entry = self._entries[index]
        if entry.blocking:
            raise QualityError(
                f"{entry.expectation} is a hard block and cannot be released. "
                f"REQ-NFR-012: an itinerary item referencing an unresolved location "
                f"is not made safe by a curator looking at it"
            )
        if self.store is not None:
            self.store.mark_released(entry, actor=actor)
        released = QuarantinedBatch(
            organization_id=entry.organization_id,
            source_id=entry.source_id,
            expectation=entry.expectation,
            failure_detail=entry.failure_detail,
            record_count=entry.record_count,
            blocking=entry.blocking,
            at=entry.at,
            released_by=actor,
        )
        self._entries[index] = released
        return released
