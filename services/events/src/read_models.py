"""Writing a folded projection to its table — STEP-007.05 (REQ-EVID-006, REQ-DATA-010).

WHY THIS IS NOT IN `projections.py`

    `projections.py` is asserted **pure**: `reads_only_its_arguments` AST-walks it
    and fails if it calls `now`, `execute`, `fetchall` or `getenv`. That rule is the
    load-bearing part of `REQ-DATA-010` — a fold that queries current state produces
    today's answer while replaying a year-old event, the rebuild completes, the
    numbers differ, and nothing points at the cause.

    Persistence is impure by definition. Putting it beside the fold would either
    break the purity check or, worse, provoke somebody into relaxing it. So the fold
    stays a function of its arguments and the write lives here, one import away.

WHY IT EXISTS AT ALL

    Until STEP-007.05 there was **no production code that wrote
    `coverage_read_model`.** `fold_coverage` folded `EVT-008` into an in-memory dict
    and nothing carried it to the table `API-017` reads, so a provider degrading
    changed a projection nobody could observe.

    The rule for how to write it did exist — inside a test
    (`test_rebuilding_restores_derived_fields_without_destroying_declared_ones`),
    as inline SQL. A rule whose only statement is in a test is a rule production
    code cannot obey.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol


class ReadModelError(RuntimeError):
    """A read-model write was refused. Nothing was partially applied."""


class Cursor(Protocol):
    """The slice of a DB-API cursor used here."""

    def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...
    def fetchall(self) -> list[tuple[Any, ...]]: ...


#: The derived half of `coverage_read_model` — folded from `EVT-008`, and the only
#: columns this module is permitted to touch.
DERIVED_COVERAGE_COLUMNS = ("freshness", "accepting_trips", "limitations")

#: The declared half — the product's statement about what it supports. No event
#: produces these, so a rebuild cannot reconstruct them and a writer must never
#: assume it can.
DECLARED_COVERAGE_COLUMNS = ("display_name", "date_bounds_start", "date_bounds_end", "time_zone")


def apply_coverage_state(cursor: Cursor, state: Mapping[str, Any]) -> frozenset[str]:
    """Write a folded coverage state to `coverage_read_model`. Returns what changed.

    UPDATE ONLY. NEVER DELETE-AND-REINSERT, AND NEVER INSERT.

        Delete-and-reinsert is the natural implementation — it is how you guarantee
        no stale row survives — and here it would erase every region's name, dates
        and zone, because those are declared and no event carries them. The result
        is a projection that rebuilds perfectly and a coverage page that cannot
        render. `STEP-006.09` asserted this and `BR-064` §4 records that the
        assertion lived only in a test until now.

        INSERT is refused from the other direction: a region nobody declared has no
        name, no dates and no zone, so inserting one would publish a region the
        product never claimed to support — with health information attached. Health
        for an undeclared region is dropped on the floor, and the return value is
        how a caller notices.

    THE `IS DISTINCT FROM` GUARD IS NOT AN OPTIMISATION

        It is what makes the return value mean "changed" rather than "was written
        to". A caller uses this set to decide whether to invalidate a cache
        (`REQ-EVID-006`), and a writer that reported every row every time would
        either bust the cache on every poll or teach the caller to ignore the
        signal. `IS DISTINCT FROM` rather than `<>` because NULL is a real value in
        `limitations` and `NULL <> NULL` is NULL, which is not true and therefore
        not an update.
    """
    changed: set[str] = set()
    for region_id, row in state.items():
        if not isinstance(row, Mapping) or "freshness" not in row:
            raise ReadModelError(
                f"region {region_id!r} has no freshness. A projection row without the "
                f"column it exists to carry is a fold that changed shape, and writing "
                f"it would put a NULL where a public enum is read."
            )
        freshness = row["freshness"]
        accepting = row.get("accepting_trips", freshness != "stale")
        # `limitations` is `jsonb`, not `text[]`. A Python list adapts to a Postgres
        # ARRAY literal — `{"a","b"}` — which is not valid JSON, so it is serialised
        # here and cast explicitly rather than left to parameter-type inference.
        # The cast is on both sides for the same reason: a row comparison against an
        # un-typed parameter does not reliably infer `jsonb`, and an inference that
        # worked by accident would be one schema change from silently comparing text.
        limitations = json.dumps(list(row.get("limitations", [])))
        cursor.execute(
            """
            UPDATE coverage_read_model
               SET freshness       = %s,
                   accepting_trips = %s,
                   limitations     = %s::jsonb
             WHERE region_id = %s
               AND (freshness, accepting_trips, limitations)
                   IS DISTINCT FROM (%s, %s, %s::jsonb)
            RETURNING region_id
            """,
            (
                freshness,
                accepting,
                limitations,
                region_id,
                freshness,
                accepting,
                limitations,
            ),
        )
        if cursor.fetchall():
            changed.add(region_id)
    return frozenset(changed)
