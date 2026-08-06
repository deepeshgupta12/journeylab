---
sub_step_id: STEP-002.03
parent_step: STEP-002
title: Role and attribute policy definitions
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-004]
blast_radius_id: BR-012
depends_on: [STEP-002.02]
last_updated: 2026-08-06
---

# STEP-002.03 — Role and attribute policy definitions

## 1. Outcome
Authorization decisions are made by one policy module derived from [AUTHORIZATION_MATRIX](../../../04-contracts/AUTHORIZATION_MATRIX.md), and the matrix generates the tests — so a matrix change without a test change fails CI.

## 2. Scope and boundary
**In scope:** `apps/api/src/authz/` (**Python — see `ADR-012`;** the TypeScript path originally named here could not satisfy `REQ-SEC-004`'s server-side requirement), role capability + resource relationship evaluation, matrix-driven test generation.
**Not in this sub-step:** provisioning (`.04`), four-eyes approval (`STEP-021`), delegated advisor access (`STEP-028`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-004 | Every operation enforces role **and** resource-relationship checks server-side | TST-SEC-004 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **RUNNABLE** — `impact(RequestContext, upstream, 3)` returned `epistemic: exact`, risk LOW, 4 direct dependents. First non-`BLOCKED` pre-change check in the repository |
| Queries run | KG-Q-015; KG-Q-014 (authorization paths) |
| Direct dependents | Every endpoint |
| Unknown / low-confidence areas | Guest-session capability model — a guest token is a bearer capability and needs an explicit expiry decision |
| Blast radius | [BR-012](../../../10-logs/blast-radius/BR-012-authorization-policy.md) — **HIGH** |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [x] Encode the nine roles — including `service`, which has **no matrix column** and is therefore denied all 22 operations
- [x] Three-check evaluation in that order. **Tenant first is a security property**: it keeps `cross_tenant_attempt` distinguishable for `ALRT-SEC-001`
- [x] **Owner-only operations** modelled explicitly and tested against editor, viewer and advisor
- [x] Guest capability requires a **timezone-aware** expiry; absent, naive or past ⇒ denied
- [x] Went further: the **matrix generates the decision table itself**, so there is no hand-transcribed copy. Drift fails CI in both directions
- [x] Deny-by-default — unlisted pair, unknown role, unproven condition and unrecognised condition name all deny

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
- [x] Sub-step record · `IMPL-010` · `BR-012` · `ADR-012` · `DEC-010` · regression entry · tracker
- [x] `AUTHORIZATION_MATRIX` §3 carries an explicit note that it is executable and how to regenerate

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | **PASS** | `pnpm verify`; 276 tests |
| R7 | **PASS — 12/12** | Policy adds a second, independent tenant check above the database |
| R2–R6 | **PASS / N/A** | R2 N/A (no contracts). See [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) |

## 11. Rollback
Policy is code; revert restores the prior version. **Loosening a policy is a security regression** requiring owner approval, not a routine revert.

## 12. Acceptance criteria
- [x] All nine roles encoded
- [x] All 176 cells exercised individually, not sampled
- [x] Deny-by-default proven, including `service` denied all 22
- [x] Owner-only operations refused to editor, viewer and advisor
- [x] Guest capability bounded and expiring; naive datetimes rejected rather than guessed

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-06 |
| Implementation | [IMPL-010](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 247 added (276 total); all 176 cells; 6/6 mutants killed |
| Decisions raised | [ADR-012](../../../../adr/ADR-012-authorization-policy-in-python.md) (Python, not TypeScript); **`DEC-010`** (unspecified matrix cell — fails closed) |
| Notes / surprises | The prediction held: generating from the matrix is what stops drift — so the table generates the *code*, not only the tests. Two things were not predicted. **(1)** The generator refused to run because 11 conditional cells named no condition; ten resolved from §4's own rules, and the eleventh became `DEC-010` rather than a guess. **(2)** A mutant looked like it survived, but `ruff format` had reflowed the generated file and my mutation pattern matched nothing — the harness was broken, not the guard. Fourth instance in this project of a check reporting success without doing work |
| Carried gaps | Nothing forces callers to use `authorize` (STEP-004); no audit sink for `audit=True` (STEP-002.07); conditions are caller-asserted and unverified here (STEP-002.04 / STEP-021) |
