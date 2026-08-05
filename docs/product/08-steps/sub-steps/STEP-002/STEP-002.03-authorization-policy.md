---
sub_step_id: STEP-002.03
parent_step: STEP-002
title: Role and attribute policy definitions
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-004]
blast_radius_id: BR-009
depends_on: [STEP-002.02]
last_updated: 2026-08-05
---

# STEP-002.03 — Role and attribute policy definitions

## 1. Outcome
Authorization decisions are made by one policy module derived from [AUTHORIZATION_MATRIX](../../../04-contracts/AUTHORIZATION_MATRIX.md), and the matrix generates the tests — so a matrix change without a test change fails CI.

## 2. Scope and boundary
**In scope:** `packages/authz/src/policy.ts`, role capability + resource relationship evaluation, matrix-driven test generation.
**Not in this sub-step:** provisioning (`.04`), four-eyes approval (`STEP-021`), delegated advisor access (`STEP-028`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-004 | Every operation enforces role **and** resource-relationship checks server-side | TST-SEC-004 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015; KG-Q-014 (authorization paths) |
| Direct dependents | Every endpoint |
| Unknown / low-confidence areas | Guest-session capability model — a guest token is a bearer capability and needs an explicit expiry decision |
| Blast radius | BR-009 — **HIGH** |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [ ] Encode the nine roles from the authorization matrix
- [ ] Three-check evaluation: tenant scope → role capability → resource relationship
- [ ] **Owner-only operations** modelled explicitly (canonical selection, repair acceptance)
- [ ] Guest-session capabilities with expiry
- [ ] Generate authorization tests **from the matrix** so drift fails CI
- [ ] Deny-by-default: an unlisted operation is denied, never permitted

## 6. Contracts and schema changes
None — consumes matrix semantics declared in `STEP-004`.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-SEC-004 | security | Every matrix cell tested — permitted allowed, denied refused |
| — | security | An operation absent from the matrix is **denied** |
| — | security | Collaborator cannot perform owner-only operations |

## 8. Telemetry, security and accessibility
Authorization denials audited with actor, operation and reason. Client-side role checks are presentation only.

## 9. Documentation to update
- [ ] Sub-step record · logs · `BR-009` · parent §21 · tracker
- [ ] `AUTHORIZATION_MATRIX` marked as the generating source for tests

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | | STEP-001 + 002.01–.02 |
| R7 | | Must pass |
| R2–R6 | | As applicable |

## 11. Rollback
Policy is code; revert restores the prior version. **Loosening a policy is a security regression** requiring owner approval, not a routine revert.

## 12. Acceptance criteria
- [ ] All nine roles encoded
- [ ] Every matrix cell has a generated test
- [ ] Deny-by-default proven
- [ ] Owner-only operations cannot be performed by editors
- [ ] Guest capability bounded and expiring

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Notes / surprises | Generating tests from the matrix is what stops the matrix becoming documentation that drifts from behavior |
