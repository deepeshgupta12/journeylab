---
sub_step_id: STEP-001.01
parent_step: STEP-001
title: Workspace skeleton and pinned toolchain
status: VERIFIED
owners: []
requirement_ids: [REQ-PLAT-001, REQ-PLAT-002]
blast_radius_id: BR-001
depends_on: []
last_updated: 2026-08-05
---

# STEP-001.01 — Workspace skeleton and pinned toolchain

## 1. Outcome
The monorepo has its workspace structure and every toolchain version is pinned by lock file, so two engineers on different machines resolve identical dependencies.

## 2. Scope and boundary
**In scope:** `package.json`, `pnpm-workspace.yaml`, `pyproject.toml`, `uv.lock`, workspace package directories, Node and Python version pinning.
**Not in this sub-step:** lint/format config (`.02`), ownership (`.03`), local services (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-PLAT-001 | `pnpm install` and `uv sync` succeed from a clean checkout | TST-PLAT-001 |
| REQ-PLAT-002 | Lock files exist and are committed; CI rejects manifest/lock drift | TST-PLAT-002 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (index covers documentation only) |
| HEAD commit | *(record at execution)* |
| Graph indexed commit | *(record)* |
| Queries run | KG-Q-015 `detect_changes()` |
| Direct dependents | None — repository is empty of code |
| Unknown / low-confidence areas | None material; no symbols exist to depend on this |
| Blast radius | BR-001 — LOW reach, **confidence limited by BLOCKED graph** |
| Approval required? | No (additive scaffold, no consumers) |

## 5. Implementation plan
- [ ] Create `package.json` with workspace scripts and the Node 24 LTS engine constraint
- [ ] Create `pnpm-workspace.yaml` covering `apps/*`, `packages/*`, `services/*`
- [ ] Create `pyproject.toml` targeting Python 3.14 with lint/type/test tool config
- [ ] Generate and commit `pnpm-lock.yaml` and `uv.lock`
- [ ] Create empty workspace package directories with placeholder `README.md` files
- [ ] Add `.nvmrc` / `.python-version` so local versions match CI

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-001 (partial) | CI | Clean checkout installs successfully |
| TST-PLAT-002 | CI | Manifest change without lock update fails |

## 8. Telemetry, security and accessibility
Secret scanning enabled from this first commit. No telemetry or UI yet.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] `IMPLEMENTATION_LOG` entry `IMPL-001`
- [ ] `REGRESSION_LOG` entry
- [ ] `BR-001` post-change section
- [ ] Parent step §21
- [ ] `MASTER_TRACKER`

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | *(no prior suite — record as N/A with reason)* |
| R2 contract compatibility | | N/A — no contracts exist |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Baseline established |
| R5 orphan/unowned nodes | | Baseline established |
| R6 closed-bug tests | | N/A — no bugs recorded |
| R7 tenant isolation | | N/A — no application |

**Note:** N/A entries are legitimate here only because this is the first sub-step. From `.02` onward, R1 and R3 must produce real results.

## 11. Rollback
Revert the commit; the repository returns to documentation-only. No data or consumer impact.

## 12. Acceptance criteria
- [ ] `pnpm install` succeeds from a clean checkout
- [ ] `uv sync` succeeds from a clean checkout
- [ ] Lock files committed
- [ ] Node and Python versions pinned and matching CI
- [ ] Workspace resolves all package directories

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-05 |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | Yes — `pnpm verify` passes |
| Bugs found | **BUG-001** (stray markup, 110 files) — fixed, guarded, closed |
| Notes / surprises | Local Node is v25.9.0; the pinned application runtime must remain **Node 24 LTS** regardless |
