"""Repositories, transaction boundaries and tenancy — TST-SEC-001 · STEP-006.04.

WHAT THESE ARE PROTECTING
    Three rules that are cheap to state and cheaper to break:

      tenant unbound        -> the database denies every row, so the bug reads as
                               "no results" rather than as an error
      two aggregates, one
      transaction           -> works until one of them moves, and then the
                               transaction that held it together cannot exist
      unversioned update    -> the second writer wins and the first one's edit
                               disappears with no error anywhere
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field

import pytest
from domain.repositories import (
    Aggregate,
    ConcurrencyConflictError,
    OutboxRecord,
    Repository,
    RepositoryError,
    UnitOfWork,
)

ORG = "11111111-1111-1111-1111-111111111111"


@dataclass
class FakeCursor:
    """Records what was executed. The rules under test are about ordering and
    refusal, and a real connection would hide both behind a successful round trip."""

    rowcount: int = 1
    statements: list[tuple[str, tuple[object, ...]]] = field(default_factory=list)

    async def execute(self, query: str, params: tuple[object, ...] = (), /) -> object:
        self.statements.append((query, params))
        return None

    def sql(self) -> list[str]:
        return [q for q, _ in self.statements]


def event() -> OutboxRecord:
    return OutboxRecord(
        event_type="journey.trip.brief_confirmed.v1",
        payload_ids=(("trip_id", "t-1"),),
        correlation_id="corr-1",
    )


# --- tenancy -----------------------------------------------------------------------


class TestTheTenantIsBoundBeforeAnythingElse:
    @pytest.mark.asyncio
    async def test_the_binding_happens_inside_the_transaction(self) -> None:
        """`set_config(..., true)` is transaction-scoped. Outside a transaction the
        binding evaporates immediately and every query silently sees nothing."""
        cursor = FakeCursor()
        async with UnitOfWork(cursor=cursor, organization_id=ORG):
            pass
        statements = cursor.sql()
        assert statements[0] == "BEGIN"
        assert "set_config" in statements[1]
        # `true` is the is_local argument, and it is the whole guarantee. With
        # `false` the setting becomes connection-scoped and survives COMMIT, so a
        # pooled connection carries one tenant's context into the next tenant's
        # transaction — which is the leak R7 tests for at the database.
        #
        # The first version of this test asserted only that set_config was called,
        # and a mutant flipping true to false survived it. Binding happened; binding
        # correctly did not.
        assert "true" in statements[1]
        assert "false" not in statements[1]

    @pytest.mark.asyncio
    async def test_a_unit_of_work_without_a_tenant_is_refused(self) -> None:
        """The database denies every row when unbound, so the failure is
        deny-by-default rather than exposure — and that is exactly why it needs to
        raise here. An empty result looks like an answer."""
        with pytest.raises(RepositoryError, match="needs a tenant"):
            async with UnitOfWork(cursor=FakeCursor(), organization_id="  "):
                pass

    @pytest.mark.asyncio
    async def test_a_repository_cannot_be_obtained_outside_the_transaction(self) -> None:
        """The structural half: there is no path to the database that skips the
        binding, because the object that reaches it does not exist until then."""
        unit = UnitOfWork(cursor=FakeCursor(), organization_id=ORG)
        with pytest.raises(RepositoryError, match="only available inside an open unit"):
            unit.repository(Aggregate.TRIP)

    @pytest.mark.asyncio
    async def test_a_completed_unit_of_work_cannot_be_reopened(self) -> None:
        """A reusable unit of work is one that gets reopened around a different
        tenant, with the previous tenant's repository still in hand."""
        unit = UnitOfWork(cursor=FakeCursor(), organization_id=ORG)
        async with unit:
            pass
        with pytest.raises(RepositoryError, match="already completed"):
            async with unit:
                pass

    def test_the_tenant_is_not_repeated_in_the_where_clause(self) -> None:
        """RLS is the guarantee. A redundant predicate would work and would also
        make every future query's correctness depend on remembering it — a second
        place to get the same thing wrong."""
        source = inspect.getsource(Repository.load)
        assert "organization_id" not in source


# --- one aggregate per transaction ---------------------------------------------------


class TestOneAggregatePerTransaction:
    @pytest.mark.asyncio
    async def test_a_second_aggregate_is_refused(self) -> None:
        """Breaking this looks like convenience: a handler with a transaction open
        reaches for a second repository. It works until one aggregate moves to
        another database, and then the transaction cannot exist."""
        async with UnitOfWork(cursor=FakeCursor(), organization_id=ORG) as unit:
            unit.repository(Aggregate.TRIP)
            with pytest.raises(RepositoryError, match="cannot also write"):
                unit.repository(Aggregate.SCENARIO)

    @pytest.mark.asyncio
    async def test_the_same_aggregate_twice_is_fine(self) -> None:
        """The rule is one aggregate, not one repository object."""
        async with UnitOfWork(cursor=FakeCursor(), organization_id=ORG) as unit:
            assert unit.repository(Aggregate.TRIP).aggregate is Aggregate.TRIP
            assert unit.repository(Aggregate.TRIP).aggregate is Aggregate.TRIP

    def test_itinerary_items_are_not_their_own_aggregate(self) -> None:
        """They belong to a `ScenarioVersion` and are written with it. An aggregate
        list that grows to include every table has stopped meaning anything."""
        assert "itinerary_item" not in {a.value for a in Aggregate}


# --- the outbox boundary ---------------------------------------------------------------


class TestEventsCommitWithTheirTransaction:
    @pytest.mark.asyncio
    async def test_a_queued_event_is_written_before_commit(self) -> None:
        cursor = FakeCursor()
        async with UnitOfWork(cursor=cursor, organization_id=ORG) as unit:
            unit.repository(Aggregate.TRIP)
            unit.enqueue(event())
        statements = cursor.sql()
        assert any("INSERT INTO outbox" in s for s in statements)
        assert statements.index(next(s for s in statements if "outbox" in s)) < statements.index(
            "COMMIT"
        )

    @pytest.mark.asyncio
    async def test_a_failed_transaction_writes_no_event(self) -> None:
        """**No phantom events.** The event exists only if the state change did."""
        cursor = FakeCursor()
        with pytest.raises(ValueError, match="boom"):
            async with UnitOfWork(cursor=cursor, organization_id=ORG) as unit:
                unit.repository(Aggregate.TRIP)
                unit.enqueue(event())
                raise ValueError("boom")
        statements = cursor.sql()
        assert "ROLLBACK" in statements
        assert "COMMIT" not in statements
        assert not any("outbox" in s for s in statements)

    @pytest.mark.asyncio
    async def test_events_cannot_be_queued_outside_a_transaction(self) -> None:
        unit = UnitOfWork(cursor=FakeCursor(), organization_id=ORG)
        with pytest.raises(RepositoryError, match="inside the transaction"):
            unit.enqueue(event())


# --- optimistic concurrency ---------------------------------------------------------------


class TestOptimisticConcurrency:
    @pytest.mark.asyncio
    async def test_a_stale_version_raises_rather_than_doing_nothing(self) -> None:
        """Zero affected rows is a conflict, not a no-op. Without the version the
        second writer wins and the first one's edit vanishes with no error."""
        cursor = FakeCursor(rowcount=0)
        async with UnitOfWork(cursor=cursor, organization_id=ORG) as unit:
            repo = unit.repository(Aggregate.TRIP)
            with pytest.raises(ConcurrencyConflictError, match="was not at version"):
                await repo.update("trips", "t-1", expected_version=3)

    @pytest.mark.asyncio
    async def test_the_expected_version_reaches_the_where_clause(self) -> None:
        cursor = FakeCursor(rowcount=1)
        async with UnitOfWork(cursor=cursor, organization_id=ORG) as unit:
            repo = unit.repository(Aggregate.TRIP)
            await repo.update("trips", "t-1", expected_version=3)
        update = next(q for q, _ in cursor.statements if q.startswith("UPDATE"))
        assert "version = %s" in update

    def test_expected_version_has_no_default(self) -> None:
        """A default would make the unchecked write the easy one — and the unchecked
        write is the one that loses an edit silently."""
        parameter = inspect.signature(Repository.update).parameters["expected_version"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY

    @pytest.mark.asyncio
    async def test_a_version_below_one_is_refused(self) -> None:
        cursor = FakeCursor()
        async with UnitOfWork(cursor=cursor, organization_id=ORG) as unit:
            repo = unit.repository(Aggregate.TRIP)
            with pytest.raises(RepositoryError, match="starts at 1"):
                await repo.update("trips", "t-1", expected_version=0)


# --- refusals ---------------------------------------------------------------------------------


class TestTableNamesAreRefusedNotEscaped:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "table", ["trips; DROP TABLE users", "Trips", "trips--", "public.trips", ""]
    )
    async def test_an_unexpected_table_name_is_refused(self, table: str) -> None:
        """A table cannot be a bound parameter, so it is interpolated — which makes
        the allowlist the whole defence rather than a nicety."""
        cursor = FakeCursor()
        async with UnitOfWork(cursor=cursor, organization_id=ORG) as unit:
            repo = unit.repository(Aggregate.TRIP)
            with pytest.raises(RepositoryError, match="refusing"):
                await repo.load(table, "t-1")
