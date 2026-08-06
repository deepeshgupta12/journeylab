"""Parse AUTHORIZATION_MATRIX.md into a decision table — STEP-002.03.

Single parser, imported by both `gen_authz_matrix.py` (which writes the generated
module) and `tests/api/test_authorization_matrix_sync.py` (which proves the
generated module still matches the markdown). One implementation, so the generator
and the drift gate cannot disagree about what the document says.
"""

from __future__ import annotations

import pathlib
import re
from typing import NamedTuple

REPO = pathlib.Path(__file__).resolve().parents[1]
MATRIX_MD = REPO / "docs/product/04-contracts/AUTHORIZATION_MATRIX.md"

# Qualifier text -> condition name.
CONDITION: dict[str, str | None] = {
    "own": "own_resource",
    "public": "public_resource",
    "explicit unlock": "explicit_unlock",
    "**second curator**": "second_curator",
    "delegated": "delegation_record",
    "dsr only": "dsr_request",
    "single trip, no raw pii": "single_trip_scope",
    "facts subgraph": "facts_subgraph",
    "code graph": "code_graph_permission",
    "": None,
}

# A bare conditional cell names no condition. Resolved from the matrix's own §4
# rules where those state one, and NEVER by guesswork:
#
#   advisor          -> §4 "Advisor delegation … requires an explicit delegation record"
#   privacy_operator -> §4 "Support scoping … reconstruct exactly one trip"
#   ops_admin        -> NOTHING in §4 covers an ops_admin approving a high-impact
#       override; §4's four-eyes rule names a *second curator*. Encoding a guess would
#       be inventing authorization policy, so this maps to a condition nothing grants:
#       the cell stays conditional as the matrix says, and every call fails closed
#       until DEC-010 is answered. See BR-012 §9.
BARE_BY_ROLE: dict[str, str] = {
    "advisor": "delegation_record",
    "privacy_operator": "single_trip_scope",
    "ops_admin": "UNSPECIFIED_see_DEC_010",
}


class Cell(NamedTuple):
    allow: bool
    audit: bool
    condition: str | None


class OperationRow(NamedTuple):
    key: str
    title: str
    api: str


def slug(title: str) -> str:
    cleaned = title.replace("**", "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")


def parse_cell(raw: str, role: str) -> Cell:
    text = raw.strip()
    audit = "📋" in text
    body = text.replace("✅", "").replace("❌", "").replace("⚠️", "").replace("📋", "").strip()

    if text.startswith("❌"):
        return Cell(allow=False, audit=False, condition=None)

    key = body.lower()
    if key not in CONDITION:
        raise ValueError(f"unmapped qualifier {body!r} in cell {raw!r} (role {role})")
    condition = CONDITION[key]

    if text.startswith("⚠️"):
        if condition is None:
            condition = BARE_BY_ROLE.get(role, "")
            if not condition:
                raise ValueError(
                    f"bare conditional for role {role!r} has no documented condition; "
                    "add it to §4 of the matrix or to BARE_BY_ROLE with a citation"
                )
        return Cell(allow=True, audit=audit, condition=condition)

    if text.startswith("✅"):
        return Cell(allow=True, audit=audit, condition=condition)

    raise ValueError(f"unrecognised cell {raw!r}")


def parse_matrix() -> tuple[list[OperationRow], list[str], dict[tuple[str, str], Cell]]:
    """Return (operations, role column names, {(operation_key, role): Cell})."""
    section = MATRIX_MD.read_text().split("## 3. Operation matrix")[1].split("## 4.")[0]
    rows = [line for line in section.splitlines() if line.strip().startswith("|")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    roles = header[2:]

    operations: list[OperationRow] = []
    table: dict[tuple[str, str], Cell] = {}
    for row in [r for r in rows[2:] if r.strip()]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        title = cells[0].replace("**", "").strip()
        key = slug(title)
        operations.append(OperationRow(key=key, title=title, api=cells[1]))
        for role, raw in zip(roles, cells[2:], strict=True):
            table[(key, role)] = parse_cell(raw, role)
    return operations, roles, table
