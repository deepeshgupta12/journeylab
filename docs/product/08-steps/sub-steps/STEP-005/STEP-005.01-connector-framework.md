---
sub_step_id: STEP-005.01
parent_step: STEP-005
title: Connector framework: credentials, egress, limits, circuit breaker
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002, REQ-DATA-003, REQ-SEC-005]
blast_radius_id: BR-030
depends_on: [STEP-004.08]
last_updated: 2026-08-05
---

# STEP-005.01 — Connector framework: credentials, egress, limits, circuit breaker

## 1. Outcome
One framework provides credential rotation, egress allowlisting, rate limiting, quota budgets, checkpointing, schema validation and circuit breaking, so no adapter reimplements resilience.

## 2. Scope and boundary
**In scope:** `services/integrations/src/framework/`; secret-manager integration; SSRF protection; retry with capped backoff and jitter; circuit-breaker state machine.

**Not in this sub-step:** Individual provider adapters (`.02`–`.06`); entity resolution (`.07`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002, REQ-DATA-003, REQ-SEC-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Whether the chosen secret manager supports rotation without restart — verify before committing |
| Blast radius | BR-030 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Credential retrieval from the secret manager with rotation support
- [ ] **Egress allowlist and SSRF protection** applied to every outbound call
- [ ] Per-provider rate limit and quota budget
- [ ] Timeout on every request — no unbounded call
- [ ] Capped exponential backoff with jitter, then circuit break
- [ ] Cursor/checkpoint persistence for resumable ingestion
- [ ] Schema validation gate that **rejects, never coerces**

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-SEC-005 | security | Non-allowlisted egress blocked; SSRF payload rejected |
| TST-DATA-003 | resilience | Repeated failures trip the breaker; recovery is half-open |
| TST-DATA-002 | integration | Checkpoint resumes without duplication |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-030` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] All eleven framework capabilities implemented
- [ ] Egress allowlist enforced
- [ ] Circuit breaker trips and recovers correctly
- [ ] Schema drift rejected with an alert
- [ ] Checkpoint resume proven idempotent

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | A provider without all eleven capabilities is not integrated — 'it works in happy path' is how unmarked stale data reaches an itinerary. |
