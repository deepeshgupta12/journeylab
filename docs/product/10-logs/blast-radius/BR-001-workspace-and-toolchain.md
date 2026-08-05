# BR-001 — Workspace skeleton and pinned toolchain

| Field | Value |
| --- | --- |
| Sub-step | STEP-001.01 |
| Requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Author | Implementation session |
| Date | 2026-08-05 |

## 1. Intent
Create the monorepo workspace structure and pin the JS and Python toolchains by lock file, so two engineers on different machines resolve identical dependencies (`REQ-PLAT-001`, `REQ-PLAT-002`).

## 2. Graph state (protocol step 2)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `c37d106` |
| Graph indexed commit | `c37d106` |
| **Match?** | **Yes** — verified via `npx gitnexus status` |
| Index timestamp | 2026-08-05 17:32 |
| Coverage | 2,496 nodes / 3,419 edges — **documentation only** |
| Status | **`BLOCKED` for application code — static fallback applied** |

> Knowledge-graph pre-change check: `BLOCKED`. Static fallback applied. Dependency coverage on application symbols is **unverified** because none exist. This does not satisfy the `REQ-KG-008` release gate.

## 3. Target nodes
| Node | Type | Source location | Owner |
| --- | --- | --- | --- |
| *(none)* | — | No application symbols exist | Unassigned (`BLK-001`) |

This is the first code commit; there is nothing to depend on it yet.

## 4. Dependencies
**Inbound:** none — no source file exists.
**Outbound:** none.

Static fallback confirmation: `find . -name '*.ts' -o -name '*.py'` outside `docs/` and `.gitnexus/` returns zero results.

## 5. Impact by category
| Category | Affected | Confidence |
| --- | --- | --- |
| Requirements / scope steps | STEP-001.01; REQ-PLAT-001, REQ-PLAT-002 | High |
| Owners / consumers | None exist | High |
| Frontend routes / components | None yet — directories only | High |
| Backend services / workflows | None yet — directories only | High |
| APIs / schemas / clients | None | High |
| Events / producers / consumers | None | High |
| Tables / migrations / caches | None | High |
| Models / prompts / retrievers / evals | None | High |
| Tests / fixtures | None yet (added in `.02` and `.08`) | High |
| Services / deployments / infrastructure | None | High |
| Dashboards / alerts / runbooks | None | High |
| Documentation | `README.md` deferred to `.05`; docs updated for toolchain decisions | High |

## 6. Data-flow check
Not applicable — no authentication, tenancy, redaction, retrieval, prompt, export or deletion path is touched.

## 7. Classification
`direct` (new files) · `documentation/process` (toolchain decisions recorded as ADRs).

## 8. Risk
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 1 | Purely additive; no existing code to disturb |
| Severity if it occurs | 2 | A wrong toolchain pin is corrected by editing two files |
| Reach | 1 | No users, no services, no consumers |
| Detectability | 1 | `pnpm install` / `uv sync` fail loudly and immediately |
| Reversibility | 1 | `git revert` restores documentation-only state |
| **Confidence in this analysis** | 3 | Graph is `BLOCKED`, but the fallback is conclusive here: there are provably zero source files to depend on this |
| Customer criticality | 1 | No customer-facing surface |

**Overall: LOW**

*Justification for LOW despite `BLOCKED` graph:* the scoring rule caps risk at the level implied by confidence. Confidence is 3 rather than 1 because the graph cannot be consulted — but the static fallback is **exhaustive** here, not sampled: a filesystem scan proves no source file exists, so the inbound dependency set is empty by construction rather than by inference. LOW is therefore justified on evidence, not on optimism. This exemption does not generalise: from `STEP-001.02` onward, source files exist and the fallback becomes genuinely partial.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | How probed | Residual risk |
| --- | --- | --- | --- |
| Node 24 vs. local v25 | Local runtime was v25.9.0 | `node -v`; resolved by installing Node 24 LTS via Homebrew (owner decision) | Low — pinned in `.nvmrc` and `engines` |
| pnpm availability | Not installed; corepack absent | `command -v pnpm`, `corepack --version`; resolved by global install (owner decision) | Low — `packageManager` field pins the version |
| Python 3.14 availability | System Python is 3.10.11 | `uv python list` — 3.14.2 present via Homebrew | Low — `uv` pins per project |
| Dependency resolution under Node 24 | Not yet executed | Deferred to acceptance run | Low — fails loudly if wrong |

## 10. Required actions
| Action | Type | Owner |
| --- | --- | --- |
| Verify `pnpm install` on a clean checkout | Test | Implementer |
| Verify `uv sync` resolves Python 3.14 | Test | Implementer |
| Record toolchain decisions as ADR-009/ADR-010 | Documentation | Implementer |
| Update docs where pnpm/Node assumptions were stated | Documentation | Implementer |
| Lock-file drift CI check | Test | Deferred to `STEP-001.03`/`STEP-027` |

## 11. Approval
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Repository owner | Deepesh Gupta | **Approved** — pnpm global install + Node 24 local install, chosen 2026-08-05 | 2026-08-05 |

Risk is LOW, so no additional approval is required beyond the toolchain decisions the owner already made.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index run |
| `detect_changes()` result | Scope as expected: root config + workspace dirs |
| Expected new nodes confirmed | Yes — config files and directory READMEs |
| Unexpected consumers found | None |
| New orphan / unowned nodes | *(pending — `CODEOWNERS` arrives in `STEP-001.03`, so unowned paths are expected until then and are tracked as a known gap)* |
| Untested requirements before → after | Baseline established |
| Regression R1–R7 | **PASS** — see REGRESSION_LOG |

## 13. Disposition
| Field | Value |
| --- | --- |
| Outcome | **merged** |
| Commit / PR | STEP-001.01 commit on `main` |
| Follow-ups | Lock-file CI enforcement (`STEP-001.03`); README + Node 24 PATH note (`STEP-001.05`); **BUG-001 guard now in the fast tier** |
