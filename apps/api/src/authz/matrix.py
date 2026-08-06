"""GENERATED from docs/product/04-contracts/AUTHORIZATION_MATRIX.md — do not edit by hand.

Regenerate with `python3 tools/gen_authz_matrix.py`.
`tests/api/test_authorization_matrix_sync.py` re-parses the markdown and fails if this
file and the matrix disagree on any cell, so a matrix change without a regeneration
cannot merge (STEP-002.03, REQ-SEC-004).
"""

from __future__ import annotations

from .roles import Operation, Role, Rule

OPERATIONS: dict[Operation, str] = {
    Operation.CREATE_TRIP: "API-001",
    Operation.READ_TRIP: "API-002",
    Operation.REPLACE_BRIEF: "API-003",
    Operation.BUILD_EVIDENCE_PACK: "API-004",
    Operation.GENERATE_SCENARIOS: "API-005",
    Operation.LIST_READ_SCENARIOS: "API-006/007",
    Operation.SELECT_CANONICAL_SCENARIO: "API-008",
    Operation.CREATE_WHAT_IF_EDIT: "API-009",
    Operation.MODIFY_PROTECTED_ITEM: "API-009",
    Operation.INVITE_COLLABORATOR: "API-010",
    Operation.BOOKING_HANDOFF: "API-011",
    Operation.ACTIVATE_LIVE_TRIP: "API-012",
    Operation.GENERATE_REPAIRS: "API-013",
    Operation.ACCEPT_REPAIR: "API-013",
    Operation.SUBMIT_FEEDBACK: "API-014",
    Operation.EXPORT_DELETE_OWN_DATA: "API-015",
    Operation.OVERRIDE_DESTINATION_FACT: "API-016",
    Operation.APPROVE_HIGH_IMPACT_OVERRIDE: "API-016",
    Operation.READ_COVERAGE: "API-017",
    Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL: "—",
    Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE: "—",
    Operation.QUERY_KNOWLEDGE_GRAPH: "API-018",
}

MATRIX: dict[tuple[Operation, Role], Rule] = {
    (Operation.CREATE_TRIP, Role.GUEST): Rule(allow=True, audit=False, condition="own_resource"),
    (Operation.CREATE_TRIP, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.CREATE_TRIP, Role.TRIP_EDITOR): Rule(allow=False, audit=False, condition=None),
    (Operation.CREATE_TRIP, Role.TRIP_VIEWER): Rule(allow=False, audit=False, condition=None),
    (Operation.CREATE_TRIP, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.CREATE_TRIP, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.CREATE_TRIP, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.CREATE_TRIP, Role.PRIVACY_OPERATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.READ_TRIP, Role.GUEST): Rule(allow=True, audit=False, condition="own_resource"),
    (Operation.READ_TRIP, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_TRIP, Role.TRIP_EDITOR): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_TRIP, Role.TRIP_VIEWER): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_TRIP, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.READ_TRIP, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.READ_TRIP, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.READ_TRIP, Role.PRIVACY_OPERATOR): Rule(
        allow=True, audit=True, condition="dsr_request"
    ),
    (Operation.REPLACE_BRIEF, Role.GUEST): Rule(allow=True, audit=False, condition="own_resource"),
    (Operation.REPLACE_BRIEF, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.REPLACE_BRIEF, Role.TRIP_EDITOR): Rule(allow=True, audit=False, condition=None),
    (Operation.REPLACE_BRIEF, Role.TRIP_VIEWER): Rule(allow=False, audit=False, condition=None),
    (Operation.REPLACE_BRIEF, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.REPLACE_BRIEF, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.REPLACE_BRIEF, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.REPLACE_BRIEF, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.BUILD_EVIDENCE_PACK, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.BUILD_EVIDENCE_PACK, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.BUILD_EVIDENCE_PACK, Role.TRIP_EDITOR): Rule(
        allow=True, audit=False, condition=None
    ),
    (Operation.BUILD_EVIDENCE_PACK, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.BUILD_EVIDENCE_PACK, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.BUILD_EVIDENCE_PACK, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.BUILD_EVIDENCE_PACK, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.BUILD_EVIDENCE_PACK, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.GENERATE_SCENARIOS, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.GENERATE_SCENARIOS, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.GENERATE_SCENARIOS, Role.TRIP_EDITOR): Rule(allow=True, audit=False, condition=None),
    (Operation.GENERATE_SCENARIOS, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.GENERATE_SCENARIOS, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.GENERATE_SCENARIOS, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.GENERATE_SCENARIOS, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.GENERATE_SCENARIOS, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.LIST_READ_SCENARIOS, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.LIST_READ_SCENARIOS, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.LIST_READ_SCENARIOS, Role.TRIP_EDITOR): Rule(
        allow=True, audit=False, condition=None
    ),
    (Operation.LIST_READ_SCENARIOS, Role.TRIP_VIEWER): Rule(
        allow=True, audit=False, condition=None
    ),
    (Operation.LIST_READ_SCENARIOS, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.LIST_READ_SCENARIOS, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.LIST_READ_SCENARIOS, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.LIST_READ_SCENARIOS, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.TRIP_OWNER): Rule(
        allow=True, audit=False, condition=None
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.ADVISOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.CURATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.OPS_ADMIN): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.SELECT_CANONICAL_SCENARIO, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.CREATE_WHAT_IF_EDIT, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.CREATE_WHAT_IF_EDIT, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.CREATE_WHAT_IF_EDIT, Role.TRIP_EDITOR): Rule(
        allow=True, audit=False, condition=None
    ),
    (Operation.CREATE_WHAT_IF_EDIT, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.CREATE_WHAT_IF_EDIT, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.CREATE_WHAT_IF_EDIT, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.CREATE_WHAT_IF_EDIT, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.CREATE_WHAT_IF_EDIT, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.MODIFY_PROTECTED_ITEM, Role.GUEST): Rule(
        allow=True, audit=False, condition="explicit_unlock"
    ),
    (Operation.MODIFY_PROTECTED_ITEM, Role.TRIP_OWNER): Rule(
        allow=True, audit=False, condition="explicit_unlock"
    ),
    (Operation.MODIFY_PROTECTED_ITEM, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.MODIFY_PROTECTED_ITEM, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.MODIFY_PROTECTED_ITEM, Role.ADVISOR): Rule(allow=False, audit=False, condition=None),
    (Operation.MODIFY_PROTECTED_ITEM, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.MODIFY_PROTECTED_ITEM, Role.OPS_ADMIN): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.MODIFY_PROTECTED_ITEM, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.INVITE_COLLABORATOR, Role.GUEST): Rule(allow=False, audit=False, condition=None),
    (Operation.INVITE_COLLABORATOR, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.INVITE_COLLABORATOR, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.INVITE_COLLABORATOR, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.INVITE_COLLABORATOR, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.INVITE_COLLABORATOR, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.INVITE_COLLABORATOR, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.INVITE_COLLABORATOR, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.BOOKING_HANDOFF, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.BOOKING_HANDOFF, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.BOOKING_HANDOFF, Role.TRIP_EDITOR): Rule(allow=True, audit=False, condition=None),
    (Operation.BOOKING_HANDOFF, Role.TRIP_VIEWER): Rule(allow=False, audit=False, condition=None),
    (Operation.BOOKING_HANDOFF, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.BOOKING_HANDOFF, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.BOOKING_HANDOFF, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.BOOKING_HANDOFF, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.ACTIVATE_LIVE_TRIP, Role.GUEST): Rule(allow=False, audit=False, condition=None),
    (Operation.ACTIVATE_LIVE_TRIP, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.ACTIVATE_LIVE_TRIP, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.ACTIVATE_LIVE_TRIP, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.ACTIVATE_LIVE_TRIP, Role.ADVISOR): Rule(allow=False, audit=False, condition=None),
    (Operation.ACTIVATE_LIVE_TRIP, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.ACTIVATE_LIVE_TRIP, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.ACTIVATE_LIVE_TRIP, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.GENERATE_REPAIRS, Role.GUEST): Rule(allow=False, audit=False, condition=None),
    (Operation.GENERATE_REPAIRS, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.GENERATE_REPAIRS, Role.TRIP_EDITOR): Rule(allow=True, audit=False, condition=None),
    (Operation.GENERATE_REPAIRS, Role.TRIP_VIEWER): Rule(allow=False, audit=False, condition=None),
    (Operation.GENERATE_REPAIRS, Role.ADVISOR): Rule(
        allow=True, audit=True, condition="delegation_record"
    ),
    (Operation.GENERATE_REPAIRS, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.GENERATE_REPAIRS, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.GENERATE_REPAIRS, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.ACCEPT_REPAIR, Role.GUEST): Rule(allow=False, audit=False, condition=None),
    (Operation.ACCEPT_REPAIR, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.ACCEPT_REPAIR, Role.TRIP_EDITOR): Rule(allow=False, audit=False, condition=None),
    (Operation.ACCEPT_REPAIR, Role.TRIP_VIEWER): Rule(allow=False, audit=False, condition=None),
    (Operation.ACCEPT_REPAIR, Role.ADVISOR): Rule(allow=False, audit=False, condition=None),
    (Operation.ACCEPT_REPAIR, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.ACCEPT_REPAIR, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.ACCEPT_REPAIR, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.SUBMIT_FEEDBACK, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.SUBMIT_FEEDBACK, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.SUBMIT_FEEDBACK, Role.TRIP_EDITOR): Rule(allow=True, audit=False, condition=None),
    (Operation.SUBMIT_FEEDBACK, Role.TRIP_VIEWER): Rule(allow=True, audit=False, condition=None),
    (Operation.SUBMIT_FEEDBACK, Role.ADVISOR): Rule(allow=False, audit=False, condition=None),
    (Operation.SUBMIT_FEEDBACK, Role.CURATOR): Rule(allow=False, audit=False, condition=None),
    (Operation.SUBMIT_FEEDBACK, Role.OPS_ADMIN): Rule(allow=False, audit=False, condition=None),
    (Operation.SUBMIT_FEEDBACK, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.GUEST): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.TRIP_OWNER): Rule(
        allow=True, audit=False, condition=None
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.TRIP_EDITOR): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.TRIP_VIEWER): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.ADVISOR): Rule(
        allow=True, audit=False, condition="own_resource"
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.CURATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.OPS_ADMIN): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.EXPORT_DELETE_OWN_DATA, Role.PRIVACY_OPERATOR): Rule(
        allow=True, audit=True, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.GUEST): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.TRIP_OWNER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.ADVISOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.CURATOR): Rule(
        allow=True, audit=True, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.OPS_ADMIN): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.OVERRIDE_DESTINATION_FACT, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.GUEST): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.TRIP_OWNER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.ADVISOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.CURATOR): Rule(
        allow=True, audit=False, condition="second_curator"
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.OPS_ADMIN): Rule(
        allow=True, audit=True, condition="UNSPECIFIED_see_DEC_010"
    ),
    (Operation.APPROVE_HIGH_IMPACT_OVERRIDE, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_COVERAGE, Role.GUEST): Rule(
        allow=True, audit=False, condition="public_resource"
    ),
    (Operation.READ_COVERAGE, Role.TRIP_OWNER): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_COVERAGE, Role.TRIP_EDITOR): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_COVERAGE, Role.TRIP_VIEWER): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_COVERAGE, Role.ADVISOR): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_COVERAGE, Role.CURATOR): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_COVERAGE, Role.OPS_ADMIN): Rule(allow=True, audit=False, condition=None),
    (Operation.READ_COVERAGE, Role.PRIVACY_OPERATOR): Rule(allow=True, audit=False, condition=None),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.GUEST): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.TRIP_OWNER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.ADVISOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.CURATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.OPS_ADMIN): Rule(
        allow=True, audit=True, condition=None
    ),
    (Operation.DISABLE_PROVIDER_ROLL_BACK_MODEL, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.GUEST): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.TRIP_OWNER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.ADVISOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.CURATOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.OPS_ADMIN): Rule(
        allow=True, audit=True, condition="single_trip_scope"
    ),
    (Operation.READ_SUPPORT_DIAGNOSTIC_BUNDLE, Role.PRIVACY_OPERATOR): Rule(
        allow=True, audit=True, condition="single_trip_scope"
    ),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.GUEST): Rule(allow=False, audit=False, condition=None),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.TRIP_OWNER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.TRIP_EDITOR): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.TRIP_VIEWER): Rule(
        allow=False, audit=False, condition=None
    ),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.ADVISOR): Rule(allow=False, audit=False, condition=None),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.CURATOR): Rule(
        allow=True, audit=False, condition="facts_subgraph"
    ),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.OPS_ADMIN): Rule(
        allow=True, audit=True, condition="code_graph_permission"
    ),
    (Operation.QUERY_KNOWLEDGE_GRAPH, Role.PRIVACY_OPERATOR): Rule(
        allow=False, audit=False, condition=None
    ),
}
