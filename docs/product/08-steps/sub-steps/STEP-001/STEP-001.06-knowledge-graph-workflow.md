---
sub_step_id: STEP-001.06
parent_step: STEP-001
title: Knowledge-graph workflow wiring
status: IN_PROGRESS
owners: []
requirement_ids: [REQ-KG-003, REQ-KG-008]
blast_radius_id: BR-006
depends_on: [STEP-001.05]
last_updated: 2026-08-05
---

# STEP-001.06 — Knowledge-graph workflow wiring

> **Partially delivered.** GitNexus is installed and the repository is indexed (verified 2026-08-05). What remains is CI automation and the enforcement gate.

## 1. Outcome
GitNexus indexes this repository, the working agreement in `CLAUDE.md` documents the mandatory pre-change workflow, and CI refreshes the graph on every merge.

## 2. Scope and boundary
**In scope:** GitNexus installation and indexing, `CLAUDE.md`/`AGENTS.md` working agreement, `.gitignore` for the index, CI refresh workflow, freshness check.
**Not in this sub-step:** the full graph platform — extractors, domain graph, query API and quality gates are [STEP-026](../../STEP-026-knowledge-graph-platform.md).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-KG-003 | Graph refreshes within 10 minutes of merge | TST-KG-003 |
| REQ-KG-008 | Merge blocked without a pre-change record | TST-KG-008 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **AVAILABLE — documentation only** |
| Indexed | 2026-08-05 · **119 nodes, 143 edges**, 0 clusters, 0 flows |
| Freshness | `npx gitnexus status` → up to date at the indexed commit |
| Invocation | **`npx gitnexus <command>`** — the project-local `.gitnexus/run.cjs` runner was **not** generated (`ASM-009`) |
| Unknown / low-confidence areas | **Coverage gates are not evaluable** — no application source exists (`RISK-014`) |
| Blast radius | BR-006 — affects the safety of every future change |
| Approval required? | Yes — this establishes the enforcement gate |

## 5. Implementation plan
- [x] Install GitNexus and index the repository (`npx gitnexus analyze`)
- [x] Verify freshness (`npx gitnexus status`)
- [x] `.gitignore` entry for `.gitnexus/`
- [x] `CLAUDE.md` / `AGENTS.md` working agreement, preserving the `<!-- gitnexus:start -->` … `<!-- gitnexus:end -->` marked region so `analyze` can regenerate it without destroying repository rules
- [ ] `.github/workflows/knowledge-graph.yml` — incremental refresh on merge
- [ ] Freshness check surfacing index/HEAD divergence
- [ ] **CI gate blocking merges without a change-impact record** (`TST-KG-008`)
- [ ] Document the full command reference in `INDEXING_AND_REFRESH`

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-KG-003 | CI | Refresh completes within 10 minutes of merge |
| TST-KG-008 | CI | A pull request without a change-impact record is **blocked** |

## 8. Telemetry, security and accessibility
Index freshness monitored (`ALRT-KG-001`). **Embeddings remain disabled** until a scan proves no secret or customer payload can enter them (`REQ-KG-007`).

## 9. Documentation to update
- [x] `CLAUDE.md` working agreement
- [x] `INDEXING_AND_REFRESH` verified-state section
- [ ] Sub-step completion record · `IMPLEMENTATION_LOG` · `REGRESSION_LOG` · `BR-006` · parent §21 · tracker

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | Includes `.01`–`.05` |
| R3 graph diff as expected | | `detect_changes()` becomes usable from here |
| R4/R5 | | **Baselines established for the ratchet** |
| R2, R6, R7 | | N/A at this sub-step |

## 11. Rollback
`npx gitnexus clean` removes the index; the working agreement reverts with the commit. **Removing the enforcement gate is a governance regression** requiring owner approval.

## 12. Acceptance criteria
- [x] Repository indexed and `status` reports current
- [x] Working agreement documents the pre-change workflow and the marked-region convention
- [ ] CI refreshes the graph on merge within 10 minutes
- [ ] A pull request without a change-impact record is blocked
- [ ] Command reference documented and verified working (`npx gitnexus`, not `run.cjs`)

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | Partially — indexing and working agreement done; CI gate outstanding |
| Commit SHA | *(baseline commit)* |
| Graph re-indexed at | 2026-08-05 |
| Notes / surprises | Two findings worth carrying forward: (1) `analyze` did **not** generate `.gitnexus/run.cjs`, so the documented invocation is `npx gitnexus`; (2) `analyze` **generates and overwrites `CLAUDE.md`** inside its marker block — repository rules must live outside that block or they will be destroyed on the next index |
</content>
