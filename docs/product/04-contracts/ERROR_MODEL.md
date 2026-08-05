# JourneyLab — Error Model

| Field | Value |
| --- | --- |
| Owner | Product Architect (unassigned — `BLK-001`) |
| Status | `PROPOSED` |
| Standard | RFC 9457 problem details (`application/problem+json`) |
| Last reviewed | 2026-08-05 |

Navigation: [API contracts](API_CONTRACTS.md) · [Frontend](../03-architecture/FRONTEND_ARCHITECTURE.md) · [Operations](../07-operations/OPERATIONS_AND_SUPPORT.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Problem detail shape

```json
{
  "type": "https://journeylab.app/problems/solver.infeasible",
  "title": "No feasible scenario exists for these constraints",
  "status": 422,
  "detail": "Human-readable, safe to display, never leaking another tenant's data",
  "instance": "/v1/trips/trp_01/scenarios:generate",
  "code": "solver.infeasible",
  "correlation_id": "…",
  "retryable": false,
  "remediation": { "kind": "relax_constraints", "conflict_set": ["…"] }
}
```

| Field | Rule |
| --- | --- |
| `type` | Stable URI; **never changes meaning** once published |
| `code` | Machine-stable, dot-namespaced, used for client branching |
| `detail` | Safe for display; contains no other tenant's data, no stack trace, no provider identity |
| `correlation_id` | Always present — the single thing support needs |
| `retryable` | Explicit boolean; clients must not infer retryability from the status code |
| `remediation` | Structured, actionable next step where one exists |

**Design principle:** an error must tell the user what to do next. "Something went wrong" is not an error model — it is an apology.

---

## 2. Error taxonomy

| Class | Status | Meaning | Client behavior |
| --- | --- | --- | --- |
| Validation | 400 / 422 | Input malformed or semantically impossible | Show inline, do not retry |
| Authentication | 401 | Missing/expired credential | Re-authenticate |
| Authorization | 403 / 404 | Not permitted, or resource unknown | **Identical response** to prevent enumeration |
| Concurrency | 409 | Version conflict | Refetch, show diff, let user resolve |
| Idempotency | 409 | Key reuse with different payload | Surface as a client defect |
| Rate limit | 429 | Quota exceeded | Honour `Retry-After` |
| Domain | 422 | Valid input, impossible outcome (infeasible, out of coverage) | **Product state, not an error toast** |
| Dependency | 503 | Provider or model unavailable | Degraded mode with disclosure |
| Timeout | 504 | Operation exceeded budget | Preserve last valid state; offer retry |
| Internal | 500 | Unexpected | Generic message + correlation ID only |

---

## 3. Error code register

| Code | Status | Meaning | Remediation | Requirement |
| --- | --- | --- | --- | --- |
| `coverage.unsupported_region` | 422 | Region not in the destination pack | Show supported regions; offer waitlist | REQ-TRIP-002 |
| `coverage.unsupported_dates` | 422 | Dates outside coverage or planning window | Show supported bounds | REQ-TRIP-002 |
| `coverage.provider_degraded` | 503 | Provider health insufficient for reliable planning | **Refuse rather than produce a partial simulation** | REQ-EVID-006 |
| `constraint.ambiguous_requires_clarification` | 422 | A blocking ambiguity prevents solving | Present the specific clarification question | REQ-CONS-002 |
| `constraint.unsatisfiable` | 422 | Constraints conflict before search | Return minimal conflict set | REQ-CONS-005 |
| `solver.infeasible` | 422 | No feasible schedule exists | Minimal conflict set + suggested relaxations | REQ-CONS-005 |
| `solver.timeout` | 504 | Generation exceeded budget | Return best-known feasible or preserve last valid version | REQ-NFR-004 |
| `evidence.pack_stale` | 409 | Evidence changed since the pack was built | Rebuild pack and regenerate | REQ-EVID-005 |
| `evidence.insufficient_coverage` | 422 | Critical facts missing | State what is missing; block affected options | REQ-AI-004 |
| `evidence.conflicting_sources` | 200 + warning | Sources disagree | **Not an error** — surfaced with hierarchy | REQ-EVID-002 |
| `itinerary.item_protected` | 409 | Edit targets a protected/booked item | Require explicit unlock by the user | REQ-CONS-011 |
| `concurrency.version_mismatch` | 409 | ETag mismatch | Refetch and re-apply | — |
| `collaboration.invitation_expired` | 403 | Link expired or revoked | **Fail closed, leak nothing** | REQ-SEC-008 |
| `affiliate.unavailable` | 503 | Partner unreachable | Copyable booking details fallback | REQ-BOOK-004 |
| `booking.availability_changed` | 409 | Provider availability changed | Re-search and show a clear delta | REQ-BOOK-001 |
| `ai.schema_violation` | 500 (internal), user-invisible | Model returned invalid structure | Retry once, then non-AI fallback | REQ-AI-002 |
| `ai.budget_exceeded` | 503 (internal) | Cost/latency budget hit | Degrade to fallback | REQ-AI-008 |
| `ai.injection_detected` | internal | Untrusted instruction detected in retrieved content | Drop content, alert, exclude with reason | REQ-AI-009 |
| `privacy.deletion_failed` | 202 + tracked | Deletion incomplete | Monitored retry queue visible to privacy owner | REQ-PRIV-007 |
| `authz.forbidden` | 403/404 | Not permitted | Identical to not-found | REQ-SEC-004 |
| `tenant.isolation_violation` | 500 + **SEV1 alert** | Cross-tenant access attempted | Halt, incident response | REQ-SEC-002 |

---

## 4. Domain "errors" that are actually product states

These must **not** be rendered as failures. Treating them as errors is the exact false-confidence problem JourneyLab exists to fix.

| Condition | Correct presentation |
| --- | --- |
| `solver.infeasible` | A first-class screen: "these three constraints conflict — relaxing any one restores feasibility", with the conflict set |
| `evidence.insufficient_coverage` | Explicit statement of what could not be established, with affected options blocked and labelled |
| `evidence.conflicting_sources` | Both values shown with sources, observed times and hierarchy |
| `coverage.unsupported_region` | Honest scope statement with supported alternatives |
| Abstention by `AI-004` | "We could not verify this" — a trust signal, not a failure |

---

## 5. Logging and telemetry rules

| Rule | Reason |
| --- | --- |
| Every error logs its `correlation_id`, `code` and route template | Diagnosability without payloads |
| **Never log** request bodies containing constraints, evidence prose or personal data | `REQ-PRIV-004`, `SC-REDACT-01` |
| Provider identities are logged internally but **never returned** to clients | Commercial confidentiality and attack-surface reduction |
| `tenant.isolation_violation` triggers SEV1 immediately | `RISK-010` |
| 5xx rates feed error-budget burn; 4xx do not | Client errors are not service failures |
</content>
