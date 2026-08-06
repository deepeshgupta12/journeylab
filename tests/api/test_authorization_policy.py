"""Authorization policy behaviour — TST-SEC-004 · STEP-002.03.

The exhaustive test below walks all 176 matrix cells rather than sampling, because
AUTHORIZATION_MATRIX §6 requires TST-SEC-004 to be "matrix-driven, not sampled".
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from auth.context import RequestContext
from authz import Decision, Operation, Resource, Role, authorize, enforce
from authz.matrix import MATRIX
from fastapi import HTTPException

ORG_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
ORG_B = uuid.UUID("22222222-2222-2222-2222-222222222222")
ACTOR = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OTHER = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

CTX = RequestContext(actor_id=ACTOR, organization_id=ORG_A)
FUTURE = datetime.now(UTC) + timedelta(hours=1)
OWNED = Resource(organization_id=ORG_A, owner_id=ACTOR)


def _call(role: Role, operation: Operation, **kw: object) -> Decision:
    """Invoke authorize with every condition satisfiable, so only the matrix decides."""
    rule = MATRIX.get((operation, role))
    conditions = frozenset({rule.condition} if rule and rule.condition else set())
    defaults: dict[str, object] = {
        "context": CTX,
        "role": role,
        "operation": operation,
        "resource": OWNED,
        "satisfied_conditions": conditions,
        "prior_approver_id": OTHER,
        "guest_expires_at": FUTURE,
    }
    defaults.update(kw)
    return authorize(**defaults)  # type: ignore[arg-type]


# --- TST-SEC-004: every cell, permitted allowed and denied refused -----------

MATRIX_ROLES = [r for r in Role if r is not Role.SERVICE]


@pytest.mark.parametrize(
    ("operation", "role"),
    [(op, role) for op in Operation for role in MATRIX_ROLES if (op, role) in MATRIX],
    ids=lambda v: v.value if hasattr(v, "value") else str(v),
)
def test_every_matrix_cell_behaves_as_declared(operation: Operation, role: Role) -> None:
    rule = MATRIX[(operation, role)]
    decision = _call(role, operation)

    if not rule.allow:
        assert not decision.allowed, f"{role.value} was permitted {operation.value}"
        return

    # An UNSPECIFIED condition is documented to fail closed — see DEC-010.
    if (rule.condition or "").startswith("UNSPECIFIED_"):
        assert not decision.allowed
        assert decision.reason == "condition_unspecified_in_matrix"
        return

    assert decision.allowed, f"{role.value} was denied {operation.value}: {decision.reason}"
    assert decision.audit == rule.audit


@pytest.mark.parametrize(
    ("operation", "role"),
    [(op, role) for op in Operation for role in MATRIX_ROLES if MATRIX[(op, role)].condition],
    ids=lambda v: v.value if hasattr(v, "value") else str(v),
)
def test_conditional_cells_deny_without_their_condition(operation: Operation, role: Role) -> None:
    """A conditional permission with no proof is a denial, not a permission."""
    decision = _call(
        role,
        operation,
        satisfied_conditions=frozenset(),
        resource=Resource(organization_id=ORG_A, owner_id=OTHER),  # defeats own_resource
    )
    rule = MATRIX[(operation, role)]
    if rule.condition == "public_resource":
        assert decision.allowed  # public is self-evident by design
    else:
        assert not decision.allowed, f"{role.value}/{operation.value} allowed without condition"


# --- deny-by-default ---------------------------------------------------------


def test_service_identity_is_denied_every_operation() -> None:
    """`service` has no matrix column, so all 22 operations must refuse it."""
    allowed = [op.value for op in Operation if _call(Role.SERVICE, op).allowed]
    assert not allowed, f"service identity was permitted: {allowed}"


def test_unknown_pairing_is_denied_not_permitted() -> None:
    decision = authorize(context=CTX, role=Role.SERVICE, operation=Operation.READ_TRIP)
    assert not decision.allowed
    assert decision.reason == "no_matrix_rule"


# --- tenant scope is checked before role ------------------------------------


def test_cross_tenant_is_denied_even_for_a_permitted_role() -> None:
    decision = _call(
        Role.TRIP_OWNER,
        Operation.READ_TRIP,
        resource=Resource(organization_id=ORG_B, owner_id=ACTOR),
    )
    assert not decision.allowed
    assert decision.reason == "cross_tenant_attempt", (
        "a cross-tenant attempt must be reported as such, not as a relationship failure — "
        "ALRT-SEC-001 depends on this distinction"
    )
    assert decision.audit is True


# --- owner-only operations ---------------------------------------------------


@pytest.mark.parametrize(
    "operation",
    [Operation.SELECT_CANONICAL_SCENARIO, Operation.ACCEPT_REPAIR],
)
@pytest.mark.parametrize("role", [Role.TRIP_EDITOR, Role.TRIP_VIEWER, Role.ADVISOR])
def test_owner_only_operations_refuse_collaborators(operation: Operation, role: Role) -> None:
    """REQ-COLL-003 / REQ-LIVE-005: never delegable, never automatic."""
    assert not _call(role, operation).allowed


def test_owner_can_perform_owner_only_operations() -> None:
    assert _call(Role.TRIP_OWNER, Operation.SELECT_CANONICAL_SCENARIO).allowed
    assert _call(Role.TRIP_OWNER, Operation.ACCEPT_REPAIR).allowed


def test_own_resource_condition_rejects_someone_elses_resource() -> None:
    decision = _call(
        Role.GUEST,
        Operation.CREATE_TRIP,
        resource=Resource(organization_id=ORG_A, owner_id=OTHER),
    )
    assert not decision.allowed
    assert decision.reason == "actor_does_not_own_resource"


# --- guest capability is bounded and expires ---------------------------------


def test_guest_without_expiry_is_denied() -> None:
    decision = _call(Role.GUEST, Operation.READ_TRIP, guest_expires_at=None)
    assert not decision.allowed
    assert decision.reason == "guest_capability_has_no_expiry"


def test_expired_guest_capability_is_denied() -> None:
    decision = _call(
        Role.GUEST, Operation.READ_TRIP, guest_expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    assert not decision.allowed
    assert decision.reason == "guest_capability_expired"


def test_naive_guest_expiry_is_denied_rather_than_guessed() -> None:
    """A naive datetime has no defined instant; guessing a zone could extend a session."""
    decision = _call(Role.GUEST, Operation.READ_TRIP, guest_expires_at=datetime(2099, 1, 1))  # noqa: DTZ001
    assert not decision.allowed
    assert decision.reason == "guest_expiry_is_naive_datetime"


def test_guest_expiry_does_not_affect_other_roles() -> None:
    assert _call(Role.TRIP_OWNER, Operation.READ_TRIP, guest_expires_at=None).allowed


# --- four-eyes ---------------------------------------------------------------


def test_actor_cannot_approve_their_own_override() -> None:
    """TST-ADMIN-002 / REQ-ADMIN-002."""
    decision = _call(Role.CURATOR, Operation.APPROVE_HIGH_IMPACT_OVERRIDE, prior_approver_id=ACTOR)
    assert not decision.allowed
    assert decision.reason == "four_eyes_same_actor"


def test_four_eyes_denies_when_the_prior_actor_is_unknown() -> None:
    decision = _call(Role.CURATOR, Operation.APPROVE_HIGH_IMPACT_OVERRIDE, prior_approver_id=None)
    assert not decision.allowed
    assert decision.reason == "four_eyes_prior_actor_unknown"


def test_a_different_curator_may_approve() -> None:
    assert _call(Role.CURATOR, Operation.APPROVE_HIGH_IMPACT_OVERRIDE).allowed


def test_ops_admin_override_approval_fails_closed_pending_dec_010() -> None:
    """The matrix marks this conditional but never states the condition."""
    decision = _call(Role.OPS_ADMIN, Operation.APPROVE_HIGH_IMPACT_OVERRIDE)
    assert not decision.allowed
    assert decision.reason == "condition_unspecified_in_matrix"


# --- enforcement reuses the STEP-002.02 opaque denial ------------------------


def test_enforce_raises_the_opaque_denial_and_leaks_no_reason() -> None:
    with pytest.raises(HTTPException) as exc:
        enforce(context=CTX, role=Role.TRIP_VIEWER, operation=Operation.ACCEPT_REPAIR)
    assert exc.value.status_code == 404
    body = str(exc.value.detail).lower()
    for leak in ("role", "denied", "matrix", "forbidden", "repair"):
        assert leak not in body, f"denial leaked {leak!r}"


def test_enforce_returns_the_decision_when_permitted() -> None:
    decision = enforce(
        context=CTX,
        role=Role.TRIP_OWNER,
        operation=Operation.READ_TRIP,
        resource=OWNED,
    )
    assert decision.allowed
