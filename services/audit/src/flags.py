"""Runtime flags — STEP-002.07 (REQ-PLAT-012).

Flags change behaviour without a deployment: feature, model, provider and cohort.

CONSERVATIVE IS NOT THE SAME AS "OFF", AND GETTING IT BACKWARDS IS THE FAILURE
    The sub-step record states the trap directly: "a flag service outage that
    enables a half-built feature is a far worse outcome than one that disables a
    finished one."

    So `conservative` is a REQUIRED argument on every flag. There is no default,
    because a default would be a guess about which direction is safe, and that
    differs per flag:

        new_solver_ui   -> conservative is False (do not show unfinished UI)
        require_consent -> conservative is TRUE  (do not skip a consent gate)

    A flag whose author has not decided which way is safe cannot be evaluated.

EVERY FAILURE PATH RETURNS THE CONSERVATIVE VALUE
    Database unreachable, row missing, value malformed, wrong type — all of them.
    There is no branch that returns the permissive value on an error, and
    `evaluate` never raises.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol


class _Cursor(Protocol):
    async def execute(self, query: str, params: tuple[object, ...] = ..., /) -> object: ...
    async def fetchone(self) -> tuple[object, ...] | None: ...


@dataclass(frozen=True, slots=True)
class Flag:
    """A flag and the value to use when its real value cannot be determined.

    `conservative` has no default on purpose — see the module docstring.
    """

    key: str
    conservative: Any

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("flag key must be a non-empty string")


@dataclass(frozen=True, slots=True)
class Evaluation:
    """The value, and where it came from.

    `source` is what makes an outage visible. A caller seeing `conservative`
    everywhere knows the flag store is unreachable, rather than concluding every
    feature is genuinely switched off.
    """

    value: Any
    source: str  # "tenant" | "global" | "conservative"

    @property
    def resolved(self) -> bool:
        return self.source != "conservative"


async def evaluate(
    cur: _Cursor, flag: Flag, *, organization_id: uuid.UUID | None = None
) -> Evaluation:
    """Resolve a flag. Never raises; returns the conservative value on any doubt.

    Precedence: tenant override, then global default, then conservative.

    A single query with `ORDER BY organization_id NULLS LAST` returns the tenant
    row first when one exists — one round trip, and the precedence cannot drift
    between two separate lookups.
    """
    try:
        await cur.execute(
            """
            SELECT value, organization_id
              FROM feature_flags
             WHERE key = %s AND (organization_id = %s OR organization_id IS NULL)
             ORDER BY organization_id NULLS LAST
             LIMIT 1
            """,
            (flag.key, str(organization_id) if organization_id else None),
        )
        row = await cur.fetchone()
    except Exception:
        return Evaluation(value=flag.conservative, source="conservative")

    if row is None:
        # A missing row is NOT an error. An empty table means every feature is off,
        # which is the correct state for a system that has configured nothing.
        return Evaluation(value=flag.conservative, source="conservative")

    value, org = row[0], row[1]
    if value is None:
        return Evaluation(value=flag.conservative, source="conservative")

    return Evaluation(value=value, source="tenant" if org is not None else "global")


async def evaluate_bool(
    cur: _Cursor, flag: Flag, *, organization_id: uuid.UUID | None = None
) -> bool:
    """Resolve a flag expected to be boolean.

    A non-boolean stored value is a misconfiguration, and a misconfigured flag must
    not be interpreted generously — `{"enabled": true}` is not `true`. Anything
    that is not a real boolean falls back to conservative.
    """
    evaluation = await evaluate(cur, flag, organization_id=organization_id)
    if isinstance(evaluation.value, bool):
        return evaluation.value
    return bool(flag.conservative)
