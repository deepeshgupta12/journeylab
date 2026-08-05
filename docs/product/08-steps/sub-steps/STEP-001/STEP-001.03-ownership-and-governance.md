---
sub_step_id: STEP-001.03
parent_step: STEP-001
title: Ownership and contribution governance
status: BLOCKED
owners: []
requirement_ids: [REQ-PLAT-003]
blast_radius_id: BR-003
depends_on: [STEP-001.02]
last_updated: 2026-08-05
---

# STEP-001.03 — Ownership and contribution governance

> **`BLOCKED` by `BLK-001`.** `CODEOWNERS` requires named owners, and none exist. This sub-step cannot complete until people are assigned — it is the concrete point where the missing-owners blocker stops work.

## 1. Outcome
Every path in the repository resolves to an owner; CI rejects unowned paths; the vulnerability process and contribution rules — including the commit-attribution rule — are documented.

## 2. Scope and boundary
**In scope:** `CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`, branch protection, CI ownership check.
**Not in this sub-step:** the full release gate suite (`STEP-027`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-PLAT-003 | A path not matched by `CODEOWNERS` fails CI | TST-PLAT-003 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015; KG-Q-008 (unowned nodes) once code exists |
| Direct dependents | All future paths |
| Unknown / low-confidence areas | Owner assignment is a human decision, not a technical unknown |
| Blast radius | BR-003 — LOW technical reach, **HIGH governance reach** |
| Approval required? | Yes — repository owner must assign people |

## 5. Implementation plan
- [ ] `CODEOWNERS` covering every top-level path with a catch-all fallback
- [ ] `SECURITY.md` with the vulnerability reporting and response process
- [ ] `CONTRIBUTING.md` including:
  - [ ] sub-step workflow reference
  - [ ] **commit messages must not contain AI co-authorship attribution** (`ADR-006`)
  - [ ] pre-change impact requirement (`REQ-KG-008`)
  - [ ] regression cross-check requirement
- [ ] Branch protection on `main`: no direct pushes, required reviews, required checks
- [ ] CI check failing on unowned paths

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-003 | CI | An unowned path fails the build |
| — | CI | A commit message containing an AI co-authorship trailer is flagged |

## 8. Telemetry, security and accessibility
`SECURITY.md` establishes the disclosure channel before any code exists to be disclosed against.

## 9. Documentation to update
- [ ] Sub-step completion record · `IMPLEMENTATION_LOG` · `REGRESSION_LOG` · `BR-003` · parent §21 · tracker
- [ ] `MASTER_TRACKER` blocker `BLK-001` updated when owners are assigned

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | Includes `.01`, `.02` |
| R2–R7 | | As applicable |

## 11. Rollback
Revert governance files. **Note:** removing branch protection is a security regression and requires owner approval, not a routine revert.

## 12. Acceptance criteria
- [ ] Every path resolves to an owner
- [ ] Unowned path fails CI
- [ ] `SECURITY.md` and `CONTRIBUTING.md` published
- [ ] Branch protection active on `main`
- [ ] Commit-attribution rule documented and checked

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Blocked by | **`BLK-001` — no named owners exist** |
| Notes | This sub-step is the first hard stop in the programme. Everything before it can be built by anyone; nothing after it can be signed off by no one |
</content>
