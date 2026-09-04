"""GENERATED from docs/product/04-contracts/ERROR_MODEL.md — do not edit by hand.

Rebuild: uv run python tools/gen_error_codes.py
STEP-004.01 · REQ-PLAT-005

The register is a product document; this module is its machine form. A code
that is not in the markdown cannot be raised, and a code in the markdown that
is never raised is still declared here — the contract is the document.
"""

from __future__ import annotations

from typing import Final, NamedTuple


class ErrorCodeSpec(NamedTuple):
    """One row of the register, as data."""

    code: str
    status: int | None
    meaning: str
    remediation: str
    requirement: str | None

    @property
    def type_uri(self) -> str:
        """RFC 9457 `type`. Stable forever once published."""
        return f"https://journeylab.app/problems/{self.code}"

    @property
    def client_visible(self) -> bool:
        """False when the condition never reaches the caller as an HTTP error."""
        return self.status is not None


ERROR_CODES: Final[dict[str, ErrorCodeSpec]] = {
    "validation.invalid_request": ErrorCodeSpec(
        code="validation.invalid_request",
        status=400,
        meaning="Request does not satisfy its schema",
        remediation="Show the offending fields inline; do not retry unchanged",
        requirement="REQ-PLAT-005",
    ),
    "validation.invalid_party": ErrorCodeSpec(
        code="validation.invalid_party",
        status=422,
        meaning="Party composition is well-formed but impossible",
        remediation="State which combination cannot be planned for",
        requirement="REQ-PLAT-005",
    ),
    "coverage.unsupported_region": ErrorCodeSpec(
        code="coverage.unsupported_region",
        status=422,
        meaning="Region not in the destination pack",
        remediation="Show supported regions; offer waitlist",
        requirement="REQ-TRIP-002",
    ),
    "coverage.unsupported_dates": ErrorCodeSpec(
        code="coverage.unsupported_dates",
        status=422,
        meaning="Dates outside coverage or planning window",
        remediation="Show supported bounds",
        requirement="REQ-TRIP-002",
    ),
    "coverage.provider_degraded": ErrorCodeSpec(
        code="coverage.provider_degraded",
        status=503,
        meaning="Provider health insufficient for reliable planning",
        remediation="Refuse rather than produce a partial simulation",
        requirement="REQ-EVID-006",
    ),
    "constraint.ambiguous_requires_clarification": ErrorCodeSpec(
        code="constraint.ambiguous_requires_clarification",
        status=422,
        meaning="A blocking ambiguity prevents solving",
        remediation="Present the specific clarification question",
        requirement="REQ-CONS-002",
    ),
    "constraint.unsatisfiable": ErrorCodeSpec(
        code="constraint.unsatisfiable",
        status=422,
        meaning="Constraints conflict before search",
        remediation="Return minimal conflict set",
        requirement="REQ-CONS-005",
    ),
    "solver.infeasible": ErrorCodeSpec(
        code="solver.infeasible",
        status=422,
        meaning="No feasible schedule exists",
        remediation="Minimal conflict set + suggested relaxations",
        requirement="REQ-CONS-005",
    ),
    "solver.timeout": ErrorCodeSpec(
        code="solver.timeout",
        status=504,
        meaning="Generation exceeded budget",
        remediation="Return best-known feasible or preserve last valid version",
        requirement="REQ-NFR-004",
    ),
    "evidence.pack_stale": ErrorCodeSpec(
        code="evidence.pack_stale",
        status=409,
        meaning="Evidence changed since the pack was built",
        remediation="Rebuild pack and regenerate",
        requirement="REQ-EVID-005",
    ),
    "evidence.insufficient_coverage": ErrorCodeSpec(
        code="evidence.insufficient_coverage",
        status=422,
        meaning="Critical facts missing",
        remediation="State what is missing; block affected options",
        requirement="REQ-AI-004",
    ),
    "evidence.conflicting_sources": ErrorCodeSpec(
        code="evidence.conflicting_sources",
        status=None,
        meaning="Sources disagree",
        remediation="Not an error \u2014 surfaced with hierarchy",
        requirement="REQ-EVID-002",
    ),
    "itinerary.item_protected": ErrorCodeSpec(
        code="itinerary.item_protected",
        status=409,
        meaning="Edit targets a protected/booked item",
        remediation="Require explicit unlock by the user",
        requirement="REQ-CONS-011",
    ),
    "concurrency.version_mismatch": ErrorCodeSpec(
        code="concurrency.version_mismatch",
        status=409,
        meaning="ETag mismatch",
        remediation="Refetch and re-apply",
        requirement=None,
    ),
    "collaboration.invitation_expired": ErrorCodeSpec(
        code="collaboration.invitation_expired",
        status=403,
        meaning="Link expired or revoked",
        remediation="Fail closed, leak nothing",
        requirement="REQ-SEC-008",
    ),
    "affiliate.unavailable": ErrorCodeSpec(
        code="affiliate.unavailable",
        status=503,
        meaning="Partner unreachable",
        remediation="Copyable booking details fallback",
        requirement="REQ-BOOK-004",
    ),
    "platform.dependency_unavailable": ErrorCodeSpec(
        code="platform.dependency_unavailable",
        status=503,
        meaning="A store the operation needs is unreachable",
        remediation="Retryable; the detail names no host, DSN or driver message",
        requirement="REQ-NFR-005",
    ),
    "booking.availability_changed": ErrorCodeSpec(
        code="booking.availability_changed",
        status=409,
        meaning="Provider availability changed",
        remediation="Re-search and show a clear delta",
        requirement="REQ-BOOK-001",
    ),
    "ai.schema_violation": ErrorCodeSpec(
        code="ai.schema_violation",
        status=None,
        meaning="Model returned invalid structure",
        remediation="Retry once, then non-AI fallback",
        requirement="REQ-AI-002",
    ),
    "ai.budget_exceeded": ErrorCodeSpec(
        code="ai.budget_exceeded",
        status=None,
        meaning="Cost/latency budget hit",
        remediation="Degrade to fallback",
        requirement="REQ-AI-008",
    ),
    "ai.injection_detected": ErrorCodeSpec(
        code="ai.injection_detected",
        status=None,
        meaning="Untrusted instruction detected in retrieved content",
        remediation="Drop content, alert, exclude with reason",
        requirement="REQ-AI-009",
    ),
    "privacy.deletion_failed": ErrorCodeSpec(
        code="privacy.deletion_failed",
        status=202,
        meaning="Deletion incomplete",
        remediation="Monitored retry queue visible to privacy owner",
        requirement="REQ-PRIV-007",
    ),
    "authz.forbidden": ErrorCodeSpec(
        code="authz.forbidden",
        status=403,
        meaning="Not permitted",
        remediation="Identical to not-found",
        requirement="REQ-SEC-004",
    ),
    "tenant.isolation_violation": ErrorCodeSpec(
        code="tenant.isolation_violation",
        status=500,
        meaning="Cross-tenant access attempted",
        remediation="Halt, incident response",
        requirement="REQ-SEC-002",
    ),
}

#: Codes an API response may carry. The rest are internal conditions that
#: surface as a fallback or a warning, never as an error to the caller.
CLIENT_VISIBLE: Final[frozenset[str]] = frozenset(
    code for code, spec in ERROR_CODES.items() if spec.client_visible
)
