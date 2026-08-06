"""The single authorization decision point — STEP-002.03 (REQ-SEC-004).

Every operation in the product is authorized here or not at all. The sub-step
requires three checks in order, and the order matters:

    1. tenant scope          — is the resource even in the caller's tenant?
    2. role capability       — does the matrix permit this role this operation?
    3. resource relationship — and does the caller stand in the required relation?

Tenant is checked FIRST so that a cross-tenant attempt is never evaluated against
role rules. Otherwise a `trip_owner` in tenant A asking about tenant B's trip would
pass the role check and be denied only later — and the audit record would say
"role permitted, relationship failed" rather than the truth, which is a
cross-tenant attempt requiring a SEV1 alert (`ALRT-SEC-001`, `RISK-010`).

DENY IS THE DEFAULT AND THE ONLY FALLBACK
    There is no branch that ends in "allow" without a matching matrix rule. An
    unknown operation, an unknown role, a role with no column (`service`), or a
    condition nobody can satisfy all reach the same place.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from auth.context import RequestContext
from auth.errors import opaque_denial

from .matrix import MATRIX
from .roles import SELF_EVIDENT_CONDITIONS, UNSPECIFIED_PREFIX, Operation, Role


@dataclass(frozen=True, slots=True)
class Resource:
    """The thing being acted on.

    `organization_id` is required: an authorization question about a resource
    whose tenant is unknown cannot be answered safely, so the type does not allow
    it to be omitted.
    """

    organization_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    resource_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    """The outcome, plus why — for the audit log, never for the response body.

    `reason` exists to make denials investigable (§8 requires actor, operation and
    reason to be audited). It must not reach the caller: `enforce()` converts a
    denial into the opaque 404 from STEP-002.02, discarding this field.
    """

    allowed: bool
    reason: str
    audit: bool = False
    condition: str | None = None


def authorize(
    *,
    context: RequestContext,
    role: Role,
    operation: Operation,
    resource: Resource | None = None,
    satisfied_conditions: frozenset[str] = frozenset(),
    prior_approver_id: uuid.UUID | None = None,
    guest_expires_at: datetime | None = None,
    now: datetime | None = None,
) -> Decision:
    """Decide whether `role` may perform `operation` in `context`.

    Keyword-only throughout. These arguments are easy to transpose — swapping a
    role and an operation, or an actor and an owner, would be a silent
    authorization bug rather than a type error.
    """
    moment = now or datetime.now(UTC)

    # --- 1. tenant scope -----------------------------------------------------
    if resource is not None and resource.organization_id != context.organization_id:
        return Decision(allowed=False, reason="cross_tenant_attempt", audit=True)

    # --- guest capability must be bounded and unexpired ----------------------
    # Checked before the matrix: an expired capability is not a weaker permission,
    # it is no session at all.
    if role is Role.GUEST:
        if guest_expires_at is None:
            return Decision(allowed=False, reason="guest_capability_has_no_expiry", audit=True)
        if guest_expires_at.tzinfo is None:
            return Decision(allowed=False, reason="guest_expiry_is_naive_datetime", audit=True)
        if guest_expires_at <= moment:
            return Decision(allowed=False, reason="guest_capability_expired", audit=True)

    # --- 2. role capability --------------------------------------------------
    rule = MATRIX.get((operation, role))
    if rule is None:
        # Covers `service` (no matrix column) and any operation added to the enum
        # without a matrix row. Deny-by-default, REQ-SEC-004.
        return Decision(allowed=False, reason="no_matrix_rule", audit=True)
    if not rule.allow:
        return Decision(allowed=False, reason="role_denied_by_matrix", audit=rule.audit)

    # --- 3. resource relationship / conditions -------------------------------
    if rule.condition is not None:
        outcome = _check_condition(
            condition=rule.condition,
            context=context,
            resource=resource,
            satisfied_conditions=satisfied_conditions,
        )
        if outcome is not None:
            return Decision(allowed=False, reason=outcome, audit=True, condition=rule.condition)

    # --- four-eyes: the actor may never be their own approver ----------------
    # AUTHORIZATION_MATRIX §4 (REQ-ADMIN-002). Applied after the matrix so it can
    # only ever remove a permission, never grant one.
    if operation is Operation.APPROVE_HIGH_IMPACT_OVERRIDE:
        if prior_approver_id is None:
            return Decision(allowed=False, reason="four_eyes_prior_actor_unknown", audit=True)
        if prior_approver_id == context.actor_id:
            return Decision(allowed=False, reason="four_eyes_same_actor", audit=True)

    return Decision(allowed=True, reason="permitted", audit=rule.audit, condition=rule.condition)


def _check_condition(
    *,
    condition: str,
    context: RequestContext,
    resource: Resource | None,
    satisfied_conditions: frozenset[str],
) -> str | None:
    """Return a denial reason, or None when the condition holds."""
    if condition.startswith(UNSPECIFIED_PREFIX):
        # The matrix marks the cell conditional but never says on what. Inventing a
        # rule here would be inventing an authorization policy. See DEC-010.
        return "condition_unspecified_in_matrix"

    if condition == "own_resource":
        if resource is None:
            return "own_resource_required_but_no_resource_supplied"
        if resource.owner_id is None or resource.owner_id != context.actor_id:
            return "actor_does_not_own_resource"
        return None

    if condition == "public_resource":
        return None

    # Everything else must be proven by the caller. An unrecognised condition name
    # falls through to the same place, so a typo in the matrix denies rather than
    # silently permitting.
    if condition not in SELF_EVIDENT_CONDITIONS and condition not in satisfied_conditions:
        return f"condition_not_satisfied:{condition}"
    return None


def enforce(**kwargs: object) -> Decision:
    """`authorize`, but raising the opaque denial on refusal.

    The reason is deliberately dropped. STEP-002.03 §8 puts it in the audit log;
    STEP-002.02's `errors.py` explains why it must never reach the caller.
    """
    decision = authorize(**kwargs)  # type: ignore[arg-type]
    if not decision.allowed:
        raise opaque_denial()
    return decision
