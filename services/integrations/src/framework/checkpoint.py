"""Resumable ingestion — STEP-005.01 (REQ-DATA-002, TST-DATA-002).

THE PROPERTY IS "RESUMES WITHOUT DUPLICATION", NOT "RESUMES"
    Restarting from the last checkpoint is easy. Doing it without re-emitting
    records the previous run already emitted is the part that matters, because a
    duplicated departure in an evidence pack is not a cosmetic problem — the solver
    would treat it as a second sailing.

    Two rules make it work, and both are about ORDERING:

      1. The checkpoint advances only AFTER the batch it covers is durably handled.
         Advancing first turns a crash into silent data loss, which is worse than
         duplication because nothing reports it.
      2. Because of (1), a crash re-delivers the last batch. That is at-least-once,
         it is unavoidable without distributed transactions, and it is why every
         record carries an idempotency key — the same reasoning as the event
         envelope in STEP-004.05.

    So "without duplication" is a property of the pair, not of this module alone.
    This module's job is to make (1) impossible to get wrong.

WHY THE CURSOR IS OPAQUE
    A provider's pagination token is theirs. Parsing it to "improve" it couples us
    to a format they can change without notice, and the coupling only surfaces when
    a resume silently restarts from the beginning.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


class CheckpointError(Exception):
    """A checkpoint operation was refused."""


@dataclass(frozen=True, slots=True)
class Checkpoint:
    """Where a connector got to.

    `records_seen` is not used for resumption — it exists so a resume that
    re-delivers a batch is *visible* in the numbers rather than only in theory.
    """

    provider: str
    cursor: str
    updated_at: datetime
    records_seen: int = 0


class CheckpointStore(Protocol):
    """Persistence, kept behind a port.

    `DEC-007` has not chosen a platform and `STEP-006` owns canonical persistence,
    so committing this to a table now would be deciding someone else's design as a
    side effect. The in-memory implementation below is enough to prove the
    ordering property, which is the part that is easy to get wrong.
    """

    def load(self, provider: str) -> Checkpoint | None: ...
    def save(self, checkpoint: Checkpoint) -> None: ...


class InMemoryCheckpointStore:
    """Reference implementation and test double."""

    def __init__(self) -> None:
        self._by_provider: dict[str, Checkpoint] = {}

    def load(self, provider: str) -> Checkpoint | None:
        return self._by_provider.get(provider)

    def save(self, checkpoint: Checkpoint) -> None:
        self._by_provider[checkpoint.provider] = checkpoint


class ResumableRun:
    """One ingestion run, with the commit ordering enforced structurally.

    The API makes the dangerous order unavailable: there is no method that advances
    the cursor, only `commit_batch`, which requires the batch to have been handled
    first. A caller cannot advance past work it has not done without lying about
    what it did.
    """

    def __init__(self, store: CheckpointStore, provider: str) -> None:
        self._store = store
        self._provider = provider
        existing = store.load(provider)
        self._cursor = existing.cursor if existing else ""
        self._records_seen = existing.records_seen if existing else 0
        self.resumed = existing is not None

    @property
    def cursor(self) -> str:
        """Where to ask the provider to start. Empty means the beginning."""
        return self._cursor

    @property
    def records_seen(self) -> int:
        return self._records_seen

    def commit_batch(self, *, next_cursor: str, handled: int) -> None:
        """Advance, having durably handled `handled` records up to `next_cursor`.

        Call this **after** the records are safely stored, never before. A crash
        between handling and committing re-delivers the batch; a crash between
        committing and handling loses it, and only one of those is detectable.
        """
        if handled < 0:
            raise CheckpointError("handled must not be negative")
        if not next_cursor:
            raise CheckpointError(
                "refusing to commit an empty cursor: an empty cursor means 'start "
                "from the beginning', so committing one would silently restart the "
                "next run rather than resuming it"
            )
        self._cursor = next_cursor
        self._records_seen += handled
        self._store.save(
            Checkpoint(
                provider=self._provider,
                cursor=next_cursor,
                updated_at=datetime.now(UTC),
                records_seen=self._records_seen,
            )
        )
