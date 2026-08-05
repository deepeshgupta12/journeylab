---
sub_step_id: STEP-001.05
parent_step: STEP-001
title: README, architecture map and ADR-001
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-001, REQ-PLAT-004]
blast_radius_id: BR-005
depends_on: [STEP-001.04]
last_updated: 2026-08-05
---

# STEP-001.05 — README, architecture map and ADR-001

## 1. Outcome
A new engineer can orient and run the project from `README.md` alone, and the initial architecture decision is recorded as `ADR-001` with its alternatives and consequences.

## 2. Scope and boundary
**In scope:** `README.md`, `docs/adr/0001-architecture.md`, ADR index wiring into `DECISION_LOG`.
**Not in this sub-step:** the GitNexus workflow section of `CLAUDE.md` (`.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-PLAT-001 | An engineer runs everything using only README commands | TST-PLAT-001 |
| REQ-PLAT-004 | `ADR-001` exists with context, decision, options, consequences, rollback | TST-PLAT-004 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015 |
| Direct dependents | Documentation only |
| Unknown / low-confidence areas | None |
| Blast radius | BR-005 — documentation/process class |
| Approval required? | Architect approval for `ADR-001` content |

## 5. Implementation plan
- [ ] `README.md` covering product purpose, architecture map, local setup, data classifications, links to runbooks and `docs/product/`
- [ ] `docs/adr/0001-architecture.md` recording the modular monolith plus isolated workers decision, its alternatives and its **negative consequences**
- [ ] Index the ADR in `DECISION_LOG` §1
- [ ] Cross-link `00-START-HERE.md` from the README so the documentation system is discoverable

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-001 | e2e | An engineer who did not write it completes setup from the README |
| TST-PLAT-004 | review | ADR present with all required sections |

## 8. Telemetry, security and accessibility
README documents data classifications so contributors know what is sensitive before they handle it.

## 9. Documentation to update
- [ ] Sub-step completion record · `IMPLEMENTATION_LOG` · `REGRESSION_LOG` · `BR-005` · parent §21 · tracker
- [ ] `DECISION_LOG` ADR index

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | Includes `.01`–`.04` |
| R2–R7 | | As applicable |

## 11. Rollback
Revert documentation. No functional impact.

## 12. Acceptance criteria
- [~] **PARTIAL** — an executable guard proves every command, link, port and the Node path are correct and current. Whether the README is *comprehensible to a newcomer* cannot be self-certified by its author and remains outstanding.
- [x] ADRs record context, decision, options, consequences (incl. negatives), migration and rollback — 10 files in `docs/adr/`
- [x] All 10 ADRs indexed and cross-linked in `DECISION_LOG`
- [x] `README.md` links to `00-START-HERE.md` (verified by guard)

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-05 |
| Commit SHA | — |
| Notes / surprises | README written and guarded by tests/guards/readme-accuracy.sh, meta-tested three ways (bogus script, broken link, port mismatch). ADR filename deviates from the step file: established ADR-NNN numbering kept because renumbering would break ~100 cross-references (BR-005). The "newcomer can follow it" half of the acceptance criterion is NOT self-certified - it needs a second person. |
