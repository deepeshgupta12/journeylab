---
sub_step_id: STEP-010.09
parent_step: STEP-010
title: Citation span assembly
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-004]
blast_radius_id: TBD
depends_on: [STEP-010.08]
last_updated: 2026-09-04
---

# STEP-010.09 — Citation span assembly

## 1. Outcome
Every claim the product makes can be traced to the span of source text that supports it.

## 2. Scope and boundary
**In scope:** Span capture during retrieval; claim-to-span linkage; the citation payload.

**Not in this sub-step:** Rendering the drawer (`STEP-013.07`); claim validation (`STEP-013.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Span stability. A source that changes its text invalidates stored offsets, so spans need content anchoring rather than positions. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Spans captured at retrieval, with the source's observed time and licence
- [ ] **Anchored by content, not by offset** — a source that reflows must not silently re-point a citation
- [ ] Each claim links to the spans supporting it, and a claim with no span is not renderable
- [ ] Licence attribution travels with the span (`REQ-DATA-001`)
- [ ] Spans are part of the immutable pack

## 6. Contracts and schema changes
Consumes the citation shape declared in `STEP-004`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-004 | integration | Every rendered claim resolves to at least one span |
| — | unit | **A claim with no supporting span cannot be rendered** |
| — | integration | A reflowed source does not silently re-point a citation |
| — | unit | Licence attribution travels with the span |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Span counts per pack.

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
Revert the commit; claims lose their citations — a `REQ-EVID-004` regression that removes the product's trust mechanism.

## 12. Acceptance criteria
- [ ] Every claim resolves to a span
- [ ] No span, no render
- [ ] Content-anchored, not offset-anchored
- [ ] Attribution travels with the span

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
| Notes / surprises | **Offset-anchored citations rot silently.** The source reflows, the offsets still resolve, and the citation now points at a different sentence — the claim still renders, still looks cited, and is now wrong. `ENHANCEMENT_LOG` already names "skip the citation for this field" as an anti-pattern that attacks the trust mechanism; a citation pointing at the wrong text is worse, because it survives review. |
