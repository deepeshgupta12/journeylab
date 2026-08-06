"""Roles, operations and rule shape — STEP-002.03 (REQ-SEC-004).

Vocabulary only. The decision table lives in `matrix.py`, generated from
`docs/product/04-contracts/AUTHORIZATION_MATRIX.md`, and the evaluation logic lives
in `policy.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    """The nine roles from AUTHORIZATION_MATRIX §2.

    `SERVICE` is deliberately included even though the operation matrix has **no
    column for it**. That is not an oversight in this enum — it is a fact about the
    matrix, and the consequence is intentional: because `policy.authorize` denies
    any pair absent from the table, a service identity is denied all 22 operations
    until a capability is granted to it explicitly. §4 requires exactly that
    ("the narrowest capability; no service holds a blanket admin role").
    """

    GUEST = "guest"
    TRIP_OWNER = "trip_owner"
    TRIP_EDITOR = "trip_editor"
    TRIP_VIEWER = "trip_viewer"
    ADVISOR = "advisor"
    CURATOR = "curator"
    OPS_ADMIN = "ops_admin"
    PRIVACY_OPERATOR = "privacy_operator"
    SERVICE = "service"


class Operation(StrEnum):
    """The 22 operations from AUTHORIZATION_MATRIX §3."""

    CREATE_TRIP = "create_trip"
    READ_TRIP = "read_trip"
    REPLACE_BRIEF = "replace_brief"
    BUILD_EVIDENCE_PACK = "build_evidence_pack"
    GENERATE_SCENARIOS = "generate_scenarios"
    LIST_READ_SCENARIOS = "list_read_scenarios"
    SELECT_CANONICAL_SCENARIO = "select_canonical_scenario"
    CREATE_WHAT_IF_EDIT = "create_what_if_edit"
    MODIFY_PROTECTED_ITEM = "modify_protected_item"
    INVITE_COLLABORATOR = "invite_collaborator"
    BOOKING_HANDOFF = "booking_handoff"
    ACTIVATE_LIVE_TRIP = "activate_live_trip"
    GENERATE_REPAIRS = "generate_repairs"
    ACCEPT_REPAIR = "accept_repair"
    SUBMIT_FEEDBACK = "submit_feedback"
    EXPORT_DELETE_OWN_DATA = "export_delete_own_data"
    OVERRIDE_DESTINATION_FACT = "override_destination_fact"
    APPROVE_HIGH_IMPACT_OVERRIDE = "approve_high_impact_override"
    READ_COVERAGE = "read_coverage"
    DISABLE_PROVIDER_ROLL_BACK_MODEL = "disable_provider_roll_back_model"
    READ_SUPPORT_DIAGNOSTIC_BUNDLE = "read_support_diagnostic_bundle"
    QUERY_KNOWLEDGE_GRAPH = "query_knowledge_graph"


@dataclass(frozen=True, slots=True)
class Rule:
    """One cell of the operation matrix.

    `condition` names a predicate the caller must satisfy. A rule with
    `allow=True` and a condition is **not** a permission — it is a permission
    contingent on something the evaluator must be shown, and absent that proof it
    denies.
    """

    allow: bool
    audit: bool = False
    condition: str | None = None


# Conditions the evaluator resolves from the request itself rather than from a
# caller-supplied assertion. Everything else must be proven by the caller.
SELF_EVIDENT_CONDITIONS = frozenset({"own_resource", "public_resource"})

# Prefix marking a matrix cell whose condition the documentation never states.
# Nothing grants these, so they always deny. See DEC-010.
UNSPECIFIED_PREFIX = "UNSPECIFIED_"
