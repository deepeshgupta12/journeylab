---
sub_step_id: STEP-008.04
parent_step: STEP-008
title: Purpose-specific consent with independent withdrawal
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PRIV-002, REQ-PRIV-004]
blast_radius_id: TBD
depends_on: [STEP-008.03]
last_updated: 2026-09-04
---

# STEP-008.04 — Purpose-specific consent with independent withdrawal

## 1. Outcome
Each purpose is consented to separately and can be withdrawn without affecting any other.

## 2. Scope and boundary
**In scope:** `consent_records` writes; per-purpose grant and withdrawal; enforcement at the point of use.

**Not in this sub-step:** Deletion traversal (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PRIV-002, REQ-PRIV-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | The purpose vocabulary. Too coarse and withdrawal is all-or-nothing; too fine and the consent screen is unusable. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] One record per purpose per subject, as `DATA-016` models it
- [ ] **Withdrawal is a column, not a delete** — erasing the grant destroys the evidence that processing was lawful
- [ ] Enforcement at the point of use, not only at capture: a withdrawn purpose stops the processing immediately
- [ ] Withdrawal of one purpose provably leaves the others intact
- [ ] Consent state is inspectable by the subject (`.05`)

## 6. Contracts and schema changes
Writes `DATA-016`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PRIV-004 | integration | Withdrawing one purpose leaves every other purpose intact |
| — | integration | **A withdrawn purpose blocks the processing at the point of use**, not merely at capture |
| — | integration | Withdrawal preserves the original grant as evidence |
| — | unit | Processing without a matching consent record is refused |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Consent changes are audited. The audit records the purpose, never the content the consent covers.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()`; by inspection where a migration is involved |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert the commit; consent records remain and are still the lawful basis for what was collected under them.

## 12. Acceptance criteria
- [ ] Purposes are independently withdrawable
- [ ] Withdrawal is enforced at use
- [ ] The grant survives withdrawal as evidence
- [ ] No processing without a matching record

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Mutation testing | — |
| Bugs found | — |
| Notes / surprises | **Enforcing consent only at capture is the failure that looks compliant.** The checkbox is honoured, the record is written, and every job that already holds the data keeps processing it — because nothing re-reads the consent. The enforcement point has to be the *use*, which means every consumer of profile data needs the check, and that is a fan-out nobody sees on the consent screen. |
