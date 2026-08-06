"""Binding tenant context to a database session — STEP-002.02.

This is the join between the application boundary (STEP-002.02) and the database
control established in STEP-002.01. The RLS policies read `app_current_org()`,
which reads the `app.current_org` setting. This module is what sets it — and it is
the only place that should.

WHY set_config() AND NOT `SET LOCAL`
    `SET LOCAL app.current_org = $1` is a SYNTAX ERROR in PostgreSQL: SET does not
    accept bind parameters. Verified directly against PostgreSQL 18.4:

        ERROR:  syntax error at or near "$1"

    The obvious workaround is to interpolate the UUID into the SQL string. That
    puts string formatting on the tenancy boundary — the one place in the system
    where an injection would be worst. `set_config(name, value, is_local=true)` is
    a function call, so the value is a proper bind parameter, and `is_local=true`
    gives the same transaction scope as SET LOCAL.

    Cost: a round trip per transaction. Accepted — the alternative trades a
    parameterised query for a formatted one on the security boundary.

REQ-SEC-001.
"""

from __future__ import annotations

from typing import Protocol

from .context import RequestContext

# Transaction-scoped: `true` is the is_local argument. STEP-002.01 proved this does
# not survive COMMIT, which is what makes pooled connections safe.
_BIND_SQL = "SELECT set_config('app.current_org', %s, true)"


class _Cursor(Protocol):
    """The slice of a DB-API cursor this module uses.

    Structural, not a psycopg import: it keeps this module testable without a live
    connection, and keeps the driver choice (ADR-011) from spreading further than
    it must.
    """

    async def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...


async def bind_tenant(cursor: _Cursor, context: RequestContext) -> None:
    """Bind `context`'s tenant to the current transaction.

    MUST be called inside an open transaction. Outside one, `is_local=true` makes
    the setting apply to a transaction that ends immediately, so the binding
    silently evaporates and every subsequent query sees zero rows. That failure is
    deny-by-default rather than exposure, but it is still a bug, and the caller
    owning the transaction is what makes it visible.
    """
    await cursor.execute(_BIND_SQL, (str(context.organization_id),))
