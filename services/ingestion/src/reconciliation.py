"""Reconciliation, backfill and checkpointing — STEP-005.09 (REQ-DATA-002).

WHAT A MATCHING COUNT ACTUALLY PROVES

    A hundred records ingested against a hundred at the source proves that a hundred
    of something arrived. It does not prove they are the same hundred. One record
    dropped and one duplicated reconciles perfectly by count, and so does a whole
    page fetched twice while another was skipped.

    `DC-EXT-001` asks for "record count + checksum vs. provider index" for exactly
    this reason. Both methods are implemented here, and the weaker one **says so in
    its own result**: `Method.COUNT` carries the limitation as data, so a green
    verdict cannot be read as more than it is. A reconciliation that overstates what
    it checked is worse than none, because it retires the suspicion that would have
    led someone to look properly.

A SOURCE THAT CANNOT BE COUNTED IS NOT RECONCILED

    Several providers publish no total and no index. The tempting answer is to treat
    "nothing to compare against" as a pass, because the job then goes green for every
    provider and the dashboard is clean.

    It is the same shape as `ProfileUnsupported` in routing and `TransitUnavailable`
    in the transit adapter: the honest value is one that says the check did not
    happen. `Unreconciled` is that value. It is not a failure and it is not a pass —
    it is the absence of evidence, carried where it can be seen.

THE THRESHOLD CLASSIFIES; IT DOES NOT SUPPRESS

    The obvious design gives reconciliation a tolerance: under one percent, pass.
    That is how a slow leak stays invisible for a year — every run is green, the
    discrepancy grows a little, and nothing ever crosses the line in a single step.

    So every discrepancy is recorded whatever its size, and the threshold decides
    only how loudly it is reported. Zero drift and half a percent of drift are
    different results, and a system that renders them identically has thrown away
    the signal that would have shown the trend.

REPLAY SAFETY IS PROVED BY REPLAYING

    "Idempotent" is a claim, and the cheap way to make it true is to assert it in a
    docstring. `BackfillRun` records which record identities it has applied, so a
    replayed batch reports duplicates rather than applying them twice, and the test
    replays a batch rather than trusting this paragraph.
"""

from __future__ import annotations

import enum
import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from framework.checkpoint import CheckpointStore, ResumableRun


class ReconciliationError(ValueError):
    """A reconciliation or backfill operation was refused, and NOT partly applied."""


class Method(enum.StrEnum):
    """How completeness was checked, carried so a verdict is readable in context."""

    #: Totals compared. Cannot detect a swap: one dropped and one duplicated
    #: reconciles perfectly.
    COUNT = "count"
    #: Identity digests compared. Detects substitution, omission and duplication,
    #: and requires the source to publish an index.
    IDENTITY_DIGEST = "identity_digest"


class Verdict(enum.StrEnum):
    MATCHED = "matched"
    #: A difference was found. Always recorded, whatever its size.
    DISCREPANT = "discrepant"
    #: The source offers nothing to compare against. Neither pass nor fail.
    UNRECONCILED = "unreconciled"


#: Above this share of the source total, a discrepancy is an alert rather than an
#: observation. **It does not decide whether the discrepancy is recorded** — every
#: difference is recorded regardless, because a tolerance that suppresses is how a
#: slow leak stays invisible. Provisional pending `DEC-005`.
ALERT_THRESHOLD = 0.01


@dataclass(frozen=True, slots=True)
class SourceIndex:
    """What the provider says it holds.

    `identities` is optional because most sources do not publish one. When it is
    absent the strong method is unavailable and that fact travels with the result
    rather than being silently downgraded.
    """

    provider: str
    total: int
    identities: tuple[str, ...] | None = None
    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ReconciliationError(f"{self.provider}: a source total cannot be negative")
        if self.identities is not None and len(self.identities) != self.total:
            raise ReconciliationError(
                f"{self.provider}: the source index lists {len(self.identities)} "
                f"identities but claims a total of {self.total}. The source disagrees "
                f"with itself, and reconciling against it would compare our data "
                f"against a number we already know is wrong"
            )


def digest_of(identities: Iterable[str]) -> str:
    """An order-independent digest of a set of record identities.

    Sorted before hashing so two ingestions that fetched the same records in
    different orders agree. Duplicates are **kept** rather than collapsed: a set
    would hide the double-ingestion this is partly here to detect.
    """
    hasher = hashlib.sha256()
    for identity in sorted(identities):
        hasher.update(identity.encode())
        hasher.update(b"\0")
    return hasher.hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class Reconciliation:
    """One completeness check, retained as evidence.

    Frozen, and every field the verdict rests on is present. A retained result that
    records only its verdict cannot be re-examined when a later run disagrees with
    it, which is precisely when someone will want to.
    """

    provider: str
    method: Method
    verdict: Verdict
    ingested: int
    source_total: int | None
    at: datetime
    detail: str
    missing: tuple[str, ...] = ()
    unexpected: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.detail.strip():
            raise ReconciliationError("a reconciliation records what it compared and what it found")

    @property
    def difference(self) -> int:
        if self.source_total is None:
            return 0
        return self.ingested - self.source_total

    @property
    def drift(self) -> float:
        """Absolute difference as a share of the source total."""
        if not self.source_total:
            return 0.0
        return abs(self.difference) / self.source_total

    @property
    def alerts(self) -> bool:
        """Whether this is loud. Never whether it is recorded."""
        return self.verdict is Verdict.DISCREPANT and self.drift > ALERT_THRESHOLD

    @property
    def detects_substitution(self) -> bool:
        """Whether the method used could have noticed a swap.

        Published so a `MATCHED` verdict is readable for what it is. A count match
        with this False means "a hundred of something arrived", not "the right
        hundred arrived".
        """
        return self.method is Method.IDENTITY_DIGEST


def reconcile(
    *,
    provider: str,
    ingested_identities: Sequence[str],
    source: SourceIndex | None,
    at: datetime,
) -> Reconciliation:
    """Compare what we hold against what the source says it holds.

    `source=None` means the provider publishes neither a total nor an index. The
    result is `UNRECONCILED` — not a pass. Every provider with no count endpoint
    would otherwise report perfect completeness forever.
    """
    if source is not None and source.provider != provider:
        raise ReconciliationError(
            f"index is for {source.provider!r}, reconciling {provider!r}. Comparing "
            f"one provider's totals against another's is a green result that means "
            f"nothing"
        )

    ingested = len(ingested_identities)

    if source is None:
        return Reconciliation(
            provider=provider,
            method=Method.COUNT,
            verdict=Verdict.UNRECONCILED,
            ingested=ingested,
            source_total=None,
            at=at,
            detail=(
                f"{provider} publishes no total and no index, so completeness was not "
                f"checked. {ingested} records ingested. This is the absence of "
                f"evidence, not evidence of completeness"
            ),
        )

    if source.identities is not None:
        held, published = sorted(ingested_identities), sorted(source.identities)
        missing = tuple(sorted(set(published) - set(held)))
        unexpected = tuple(sorted(set(held) - set(published)))
        if digest_of(held) == digest_of(published):
            return Reconciliation(
                provider=provider,
                method=Method.IDENTITY_DIGEST,
                verdict=Verdict.MATCHED,
                ingested=ingested,
                source_total=source.total,
                at=at,
                detail=f"identity digest {digest_of(held)} matches over {ingested} records",
            )
        return Reconciliation(
            provider=provider,
            method=Method.IDENTITY_DIGEST,
            verdict=Verdict.DISCREPANT,
            ingested=ingested,
            source_total=source.total,
            at=at,
            detail=(
                f"identity digests differ: {len(missing)} missing, {len(unexpected)} unexpected"
            ),
            missing=missing,
            unexpected=unexpected,
        )

    if ingested == source.total:
        return Reconciliation(
            provider=provider,
            method=Method.COUNT,
            verdict=Verdict.MATCHED,
            ingested=ingested,
            source_total=source.total,
            at=at,
            detail=(
                f"{ingested} ingested against {source.total} at the source. Counts "
                f"only — this cannot detect a substitution, because one record "
                f"dropped and one duplicated reconciles exactly"
            ),
        )
    return Reconciliation(
        provider=provider,
        method=Method.COUNT,
        verdict=Verdict.DISCREPANT,
        ingested=ingested,
        source_total=source.total,
        at=at,
        detail=f"{ingested} ingested against {source.total} at the source",
    )


# --- backfill -------------------------------------------------------------------


class BackfillState(enum.StrEnum):
    RUNNING = "running"
    #: Stopped on purpose, with the cursor intact. Resumable.
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class BackfillProgress:
    """What a running backfill will tell you if you ask.

    `duplicates` is separate from `applied` on purpose. Collapsing them would make a
    replayed batch look like fresh progress, and a backfill that appears to advance
    while re-applying the same page is the failure this counter exists to expose.
    """

    provider: str
    state: BackfillState
    cursor: str
    applied: int
    duplicates: int
    batches: int

    @property
    def resumable(self) -> bool:
        """A cancelled run is resumable. That is the whole point of cancelling.

        A cancel that discarded the cursor would turn a pause into a restart from
        zero, which on a large backfill means nobody ever cancels — and a backfill
        nobody dares stop is a backfill that cannot be stopped.
        """
        return self.state is not BackfillState.COMPLETED and bool(self.cursor)


class BackfillRun:
    """A resumable, cancellable, replay-safe backfill over one provider.

    Built on `ResumableRun` from the connector framework rather than beside it, so
    the commit ordering that framework enforces — handle, then advance — is not
    re-implemented here with a different opinion.
    """

    def __init__(self, store: CheckpointStore, provider: str) -> None:
        self._run = ResumableRun(store, provider)
        self._provider = provider
        self._applied: set[str] = set()
        self._duplicates = 0
        self._batches = 0
        self._state = BackfillState.RUNNING

    @property
    def resumed(self) -> bool:
        return self._run.resumed

    def progress(self) -> BackfillProgress:
        return BackfillProgress(
            provider=self._provider,
            state=self._state,
            cursor=self._run.cursor,
            applied=len(self._applied),
            duplicates=self._duplicates,
            batches=self._batches,
        )

    def apply_batch(self, identities: Sequence[str], *, next_cursor: str) -> int:
        """Apply a batch, skipping identities already applied. Returns new records.

        Replay safety is here rather than in a docstring: a batch delivered twice —
        which the framework's commit ordering makes *likely*, because a crash between
        handling and committing re-delivers — applies nothing the second time and
        counts the duplicates where they can be seen.
        """
        if self._state is not BackfillState.RUNNING:
            raise ReconciliationError(
                f"{self._provider}: backfill is {self._state}, not running. Resume by "
                f"constructing a new run from the checkpoint rather than reviving this one"
            )
        fresh = [identity for identity in identities if identity not in self._applied]
        self._duplicates += len(identities) - len(fresh)
        self._applied.update(fresh)
        self._batches += 1
        self._run.commit_batch(next_cursor=next_cursor, handled=len(fresh))
        return len(fresh)

    def cancel(self) -> BackfillProgress:
        """Stop, leaving a checkpoint a later run can resume from."""
        if self._state is BackfillState.COMPLETED:
            raise ReconciliationError(f"{self._provider}: a completed backfill cannot be cancelled")
        self._state = BackfillState.CANCELLED
        return self.progress()

    def complete(self) -> BackfillProgress:
        self._state = BackfillState.COMPLETED
        return self.progress()

    def applied_identities(self) -> tuple[str, ...]:
        """What this run applied, for handing to `reconcile`."""
        return tuple(sorted(self._applied))


@dataclass
class ReconciliationLog:
    """Retained results. `REQ-DATA-002`: reconciliation results are evidence.

    Append-only by construction — there is no method that edits or removes an entry.
    A history that can be tidied is a history that will be tidied at exactly the
    moment it becomes inconvenient.
    """

    _entries: list[Reconciliation] = field(default_factory=list)

    def record(self, reconciliation: Reconciliation) -> None:
        self._entries.append(reconciliation)

    def entries(self) -> tuple[Reconciliation, ...]:
        return tuple(self._entries)

    def for_provider(self, provider: str) -> tuple[Reconciliation, ...]:
        return tuple(e for e in self._entries if e.provider == provider)

    def alerting(self) -> tuple[Reconciliation, ...]:
        return tuple(e for e in self._entries if e.alerts)

    def drift_series(self, provider: str) -> tuple[float, ...]:
        """Drift over time for one provider, oldest first.

        The reason discrepancies are recorded rather than suppressed by a tolerance:
        a leak that never crosses the alert threshold in a single run is visible here
        as a trend, and invisible anywhere else.
        """
        return tuple(e.drift for e in self.for_provider(provider))
