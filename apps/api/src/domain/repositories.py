"""Repositories and the unit of work — STEP-006.04 (REQ-SEC-001, REQ-DATA-008).

ONE AGGREGATE PER TRANSACTION, ENFORCED RATHER THAN AGREED

    The rule is easy to state and easy to break, because breaking it looks like
    convenience: a handler that already has a transaction open reaches for a second
    repository, and now two aggregates commit together. It works, until the day one
    of them lives in a different database or a different service, and then the
    transaction that quietly held the system together cannot exist.

    `UnitOfWork` records the first aggregate type it is asked for and refuses the
    second. Cross-aggregate consistency goes through the outbox (`.06`) — which is
    why the outbox is written in the *same* transaction as its one aggregate.

TENANT BINDING IS A PRECONDITION OF GETTING A REPOSITORY, NOT A STEP INSIDE ONE

    `REQ-SEC-001` puts a tenant on every row. A repository that binds the tenant in
    each method is one `SELECT` away from a leak the first time somebody adds a
    method and forgets. Here the binding happens when the unit of work opens, and a
    repository cannot be obtained outside one — so there is no code path that
    reaches the database without it.

    The database is deny-by-default underneath this (`app_current_org()` is NULL
    when unset, so no row qualifies), which means the failure mode of forgetting is
    "nothing found" rather than "everything found". This layer exists to turn that
    silent emptiness into an explicit refusal, because an empty result looks like
    an answer.

OPTIMISTIC CONCURRENCY, BECAUSE THE ALTERNATIVE IS A LOCK NOBODY RELEASES

    Two advisors editing one trip is a normal Tuesday. `expected_version` is
    required on every mutating call, the `UPDATE` carries it in its `WHERE`, and
    zero affected rows is a conflict rather than a no-op. Without the version the
    second writer silently wins and the first one's change disappears with no error
    anywhere.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field
from types import TracebackType
from typing import Protocol, Self


class RepositoryError(RuntimeError):
    """A repository or unit-of-work rule was violated. Nothing was committed."""


class ConcurrencyConflictError(RepositoryError):
    """Someone else changed this aggregate first. The caller re-reads and retries."""


class Aggregate(enum.StrEnum):
    """The transaction boundaries. One per unit of work, and no exceptions.

    `ItineraryItem` is deliberately absent: it belongs to a `ScenarioVersion` and is
    written with it. An aggregate list that grows to include every table is a list
    that has stopped meaning anything.
    """

    TRIP = "trip"
    TRIP_BRIEF = "trip_brief"
    EVIDENCE_PACK = "evidence_pack"
    SCENARIO = "scenario"
    CONSENT = "consent"


class Cursor(Protocol):
    """The slice of a DB-API cursor used here.

    Structural rather than a psycopg import, matching `auth.db`: it keeps the
    driver choice (`ADR-011`) from spreading and lets the rules be tested without
    a live connection.
    """

    async def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...
    @property
    def rowcount(self) -> int: ...


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    """An event queued inside the aggregate's own transaction.

    Held here rather than in `.06` because the *atomicity* is a property of this
    boundary: the relay is a separate concern, but "written in the same
    transaction" is decided by whoever owns the transaction.
    """

    event_type: str
    payload_ids: tuple[tuple[str, str], ...]
    correlation_id: str


@dataclass
class UnitOfWork:
    """One transaction, one aggregate, one tenant.

    Not re-entrant and not reusable: `__aexit__` marks it finished, and a second
    `__aenter__` raises. A unit of work that can be reopened is one that will be
    reopened around a different tenant.
    """

    cursor: Cursor
    organization_id: str
    _aggregate: Aggregate | None = None
    _entered: bool = False
    _finished: bool = False
    _committed: bool = False
    _outbox: list[OutboxRecord] = field(default_factory=list)

    async def __aenter__(self) -> Self:
        if self._finished:
            raise RepositoryError(
                "this unit of work has already completed. Open a new one rather than "
                "reusing it — a reusable unit of work is one that gets reopened around "
                "a different tenant"
            )
        if self._entered:
            raise RepositoryError("unit of work is already open; nesting is not supported")
        if not self.organization_id.strip():
            raise RepositoryError(
                "a unit of work needs a tenant (REQ-SEC-001). Without one the database "
                "denies every row, and an empty result looks like an answer"
            )
        self._entered = True
        await self.cursor.execute("BEGIN")
        # Bound once, here. A repository cannot be obtained outside this block, so
        # there is no path to the database that skips it.
        await self.cursor.execute(
            "SELECT set_config('app.current_org', %s, true)", (self.organization_id,)
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._entered = False
        self._finished = True
        if exc_type is not None:
            await self.cursor.execute("ROLLBACK")
            return
        # The outbox rows go in before COMMIT, inside the same transaction. If the
        # transaction fails they vanish with the state change, which is what makes
        # a phantom event impossible rather than unlikely.
        for record in self._outbox:
            await self.cursor.execute(
                "INSERT INTO outbox (organization_id, event_type, payload_ids, correlation_id) "
                "VALUES (%s, %s, %s, %s)",
                (
                    self.organization_id,
                    record.event_type,
                    _as_json(record.payload_ids),
                    record.correlation_id,
                ),
            )
        await self.cursor.execute("COMMIT")
        self._committed = True

    def repository(self, aggregate: Aggregate) -> Repository:
        """The one repository this transaction may use.

        A second, different aggregate is refused. The alternative is a transaction
        spanning two aggregates, which works right up until one of them moves.
        """
        if not self._entered:
            raise RepositoryError(
                "a repository is only available inside an open unit of work, because "
                "that is where the tenant is bound"
            )
        if self._aggregate is None:
            self._aggregate = aggregate
        elif self._aggregate is not aggregate:
            raise RepositoryError(
                f"this transaction already owns {self._aggregate}; it cannot also write "
                f"{aggregate}. Cross-aggregate consistency goes through the outbox, not "
                f"through a wider transaction"
            )
        return Repository(cursor=self.cursor, aggregate=aggregate, unit=self)

    def enqueue(self, record: OutboxRecord) -> None:
        """Queue an event to be written inside this transaction."""
        if not self._entered:
            raise RepositoryError("events are queued inside the transaction they belong to")
        self._outbox.append(record)

    @property
    def committed(self) -> bool:
        return self._committed

    @property
    def queued_events(self) -> tuple[OutboxRecord, ...]:
        return tuple(self._outbox)


def _as_json(pairs: Sequence[tuple[str, str]]) -> str:
    import json

    return json.dumps(dict(pairs), sort_keys=True)


@dataclass(frozen=True, slots=True)
class Repository:
    """Reads and writes for one aggregate, inside one bound transaction."""

    cursor: Cursor
    aggregate: Aggregate
    unit: UnitOfWork

    async def load(self, table: str, entity_id: str) -> None:
        """Read one row. RLS restricts it to the bound tenant.

        The tenant is not in the `WHERE` clause on purpose: adding it would work,
        and would also make every future query's correctness depend on remembering
        it. The policy is the guarantee; a redundant predicate is a second place to
        get it wrong.
        """
        await self.cursor.execute(
            f"SELECT * FROM {_safe_table(table)} WHERE id = %s",  # noqa: S608
            (entity_id,),
        )

    async def update(self, table: str, entity_id: str, *, expected_version: int) -> None:
        """Bump the version, or raise a conflict. There is no third outcome.

        `expected_version` is required rather than defaulted: a default would make
        the unchecked write the easy one, and the unchecked write is the one that
        loses an edit silently.
        """
        if expected_version < 1:
            raise RepositoryError("expected_version starts at 1")
        await self.cursor.execute(
            f"UPDATE {_safe_table(table)} SET version = version + 1 "  # noqa: S608
            f"WHERE id = %s AND version = %s",
            (entity_id, expected_version),
        )
        if self.cursor.rowcount == 0:
            raise ConcurrencyConflictError(
                f"{table} {entity_id} was not at version {expected_version}. Someone "
                f"changed it first; re-read and retry rather than overwriting their edit"
            )


#: Table names are interpolated (a parameter cannot name a table), so they are
#: restricted to an allowlist shape. Anything else is refused rather than escaped.
def _safe_table(table: str) -> str:
    if not table.replace("_", "").isalnum() or table != table.lower():
        raise RepositoryError(f"refusing {table!r} as a table name")
    return table
