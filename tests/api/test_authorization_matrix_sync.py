"""The matrix generates the tests — TST-SEC-004 · STEP-002.03.

STEP-002.03 §1: "the matrix generates the tests — so a matrix change without a test
change fails CI." This module is that gate.

`apps/api/src/authz/matrix.py` is generated from
`docs/product/04-contracts/AUTHORIZATION_MATRIX.md`. If someone edits the markdown
and does not regenerate, or edits the generated file by hand, these tests fail.

Two layers, because a shared parser could be wrong in both directions at once:
  1. drift  — re-derive from the markdown and compare against what is committed
  2. anchor — assert specific, hand-verified cells, so a parser that silently
              produced garbage for every cell could not pass by agreeing with itself
"""

import pytest
from authz.matrix import MATRIX, OPERATIONS
from authz.roles import Operation, Role
from authz_matrix_source import parse_matrix

MATRIX_ROLES = [
    Role.GUEST,
    Role.TRIP_OWNER,
    Role.TRIP_EDITOR,
    Role.TRIP_VIEWER,
    Role.ADVISOR,
    Role.CURATOR,
    Role.OPS_ADMIN,
    Role.PRIVACY_OPERATOR,
]


def test_generated_matrix_matches_the_markdown() -> None:
    """The drift gate. Edit the matrix without regenerating and this fails."""
    _, _, parsed_table = parse_matrix()
    parsed = {k: (c.allow, c.audit, c.condition) for k, c in parsed_table.items()}
    committed = {
        (op.value, role.value): (rule.allow, rule.audit, rule.condition)
        for (op, role), rule in MATRIX.items()
    }
    assert committed == parsed, (
        "authz/matrix.py disagrees with AUTHORIZATION_MATRIX.md. "
        "Run: python3 tools/gen_authz_matrix.py"
    )


def test_every_matrix_cell_is_covered() -> None:
    """22 operations x 8 role columns, with nothing quietly dropped."""
    assert len(OPERATIONS) == 22
    assert len(MATRIX) == 22 * 8
    missing = [
        (op.value, role.value)
        for op in Operation
        for role in MATRIX_ROLES
        if (op, role) not in MATRIX
    ]
    assert not missing, f"operations missing a rule: {missing}"


def test_service_role_has_no_matrix_column() -> None:
    """`service` is a documented role with no column — so it must be denied everything.

    Asserted rather than assumed: if a later matrix edit adds a `service` column,
    this fails and forces a deliberate decision instead of silently widening a
    workload identity's reach.
    """
    granted = [op.value for op in Operation if (op, Role.SERVICE) in MATRIX]
    assert not granted, f"service gained matrix rules without review: {granted}"


@pytest.mark.parametrize(
    ("operation", "role", "allow", "condition"),
    [
        # Hand-verified against AUTHORIZATION_MATRIX.md §3.
        (Operation.SELECT_CANONICAL_SCENARIO, Role.TRIP_OWNER, True, None),
        (Operation.SELECT_CANONICAL_SCENARIO, Role.TRIP_EDITOR, False, None),
        (Operation.ACCEPT_REPAIR, Role.TRIP_EDITOR, False, None),
        (Operation.CREATE_TRIP, Role.GUEST, True, "own_resource"),
        (Operation.READ_COVERAGE, Role.GUEST, True, "public_resource"),
        (Operation.MODIFY_PROTECTED_ITEM, Role.TRIP_OWNER, True, "explicit_unlock"),
        (Operation.READ_TRIP, Role.ADVISOR, True, "delegation_record"),
        (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.CURATOR, True, "second_curator"),
        (Operation.OVERRIDE_DESTINATION_FACT, Role.CURATOR, True, None),
        (Operation.OVERRIDE_DESTINATION_FACT, Role.OPS_ADMIN, False, None),
        (Operation.INVITE_COLLABORATOR, Role.GUEST, False, None),
        (Operation.ACTIVATE_LIVE_TRIP, Role.GUEST, False, None),
    ],
)
def test_anchor_cells(operation: Operation, role: Role, allow: bool, condition: str | None) -> None:
    """Pin specific cells so a uniformly-wrong parser cannot agree with itself."""
    rule = MATRIX[(operation, role)]
    assert rule.allow is allow
    assert rule.condition == condition


def test_audited_cells_are_marked() -> None:
    """The clipboard marker must survive into the rule, or audit obligations vanish."""
    assert MATRIX[(Operation.OVERRIDE_DESTINATION_FACT, Role.CURATOR)].audit is True
    assert MATRIX[(Operation.READ_TRIP, Role.ADVISOR)].audit is True
    assert MATRIX[(Operation.READ_TRIP, Role.TRIP_OWNER)].audit is False
