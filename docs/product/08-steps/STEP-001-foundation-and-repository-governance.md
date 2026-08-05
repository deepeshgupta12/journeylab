---
step_id: STEP-001
title: Foundation and repository governance
status: DISCOVERY
release: Phase 1
owners: []
dependencies: []
requirement_ids: [REQ-PLAT-001, REQ-PLAT-002, REQ-PLAT-003, REQ-PLAT-004]
api_ids: []
event_ids: []
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-001 — Foundation and repository governance

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A new engineer clones the repository and runs lint, type-check, tests and the (empty) application using only commands documented in `README.md`. CI rejects unlocked dependencies and unowned paths.

## 2. Why this step exists
Every later step assumes a reproducible environment, enforced ownership and contract boundaries. Retrofitting these after feature work has started means rewriting history and re-litigating boundaries. This is also where the GitNexus pre-change discipline becomes habitual rather than bolted on.

## 3. Scope
Monorepo skeleton per the portfolio reference shape; pinned toolchains for Node 24 LTS and Python 3.14; formatting, linting and strict TypeScript defaults; `CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`; local dependency stack via compose; `ADR-001`; the `CLAUDE.md`/`AGENTS.md` working agreement; GitNexus indexing wired into the workflow.

## 4. Explicit exclusions
No application code, contracts, migrations or infrastructure. Identity is [STEP-002](STEP-002-identity-tenancy-and-authorization.md); contracts are [STEP-004](STEP-004-contract-first-platform-apis.md); CI quality gates are [STEP-027](STEP-027-release-automation-and-controlled-rollout.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Staff Engineer | Repository admin | None | — |
| TPM | Repository read + ownership definition | None | — |

No customer data exists at this step.

## 6. Preconditions and dependencies
Repository created and remote configured — **done**: `https://github.com/deepeshgupta12/journeylab.git`. Blocked on `BLK-001` (no owners) for exit sign-off.

## 7. Inputs and source systems
Blueprint §19 Step 1 manifest; portfolio standard §5 repository shape; August 2026 technology baseline (revalidate per `ASM-004`).

## 8. Detailed normal workflow
1. Engineer scaffolds the workspace (`package.json`, `pnpm-workspace.yaml`, `pyproject.toml`, `uv.lock`).
2. Engineer pins toolchain versions and commits lock files.
3. Engineer adds formatting/lint/type configuration (`.editorconfig`, `biome.json`, `tsconfig.base.json`).
4. TPM defines `CODEOWNERS` covering every path.
5. Engineer adds `SECURITY.md` and `CONTRIBUTING.md` including the no-AI-attribution commit rule.
6. Engineer adds `docker-compose.dev.yml` for PostgreSQL/PostGIS, cache, object store, queue and observability.
7. Engineer writes `README.md` with setup, architecture map and data classifications.
8. Architect records `ADR-001`.
9. Engineer verifies GitNexus indexes the repository and documents the workflow in `CLAUDE.md`.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Path without an owner | CI fails | Build blocked | REQ-PLAT-003 |
| Lock file changed without manifest | CI fails | Build blocked | REQ-PLAT-002 |
| Local compose fails | Documented troubleshooting; setup is not "works on my machine" | Engineer unblocked | REQ-PLAT-001 |
| Baseline version unavailable | Record deviation in `ADR-001`; do not silently drift | Documented | ASM-004 |

## 10. State machine and lifecycle transitions
`empty repo → scaffolded → owned → verified locally → CI enforcing`. Regression to `CI enforcing` fails if any path loses an owner.

## 11. Frontend implementation
Workspace package skeleton only (`apps/web`, `packages/ui`, `packages/contracts`) with no routes or components.

## 12. Backend implementation
Service package skeletons (`apps/api`, `services/*`) with health endpoints only, sufficient to prove the app runs.

## 13. API, event and integration contracts
`NOT_APPLICABLE` at this step — contracts are defined in [STEP-004](STEP-004-contract-first-platform-apis.md). Reason: defining contracts before identity and tenancy primitives would embed an incorrect auth envelope.

## 14. Data model, migration and retention effects
None. No schema is created. `db/` exists with a README only.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. No AI is involved in repository scaffolding, and none is warranted — this is deterministic configuration work.

## 16. Security, privacy, accessibility and responsible-AI controls
Branch protection; reviewed deployments; `SECURITY.md` vulnerability process; secret scanning enabled from the first commit; no secrets in the repository; accessibility standard stated in `CONTRIBUTING.md` so it is a contribution rule, not a later audit.

## 17. Observability, analytics and KPIs
CI pass rate and local setup time (measured by asking the next engineer). No product telemetry exists yet.

## 18. Files and modules expected to change
All `PROPOSED`: `README.md`, `CLAUDE.md`, `AGENTS.md`, `package.json`, `pnpm-workspace.yaml`, `pyproject.toml`, `uv.lock`, `.editorconfig`, `biome.json`, `tsconfig.base.json`, `CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`, `docker-compose.dev.yml`, `docs/adr/0001-architecture.md`.

**Verified existing:** `CLAUDE.md` and `AGENTS.md` exist (GitNexus-generated block plus the working agreement); `.gitignore` and `.claude/skills/gitnexus/` exist.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **AVAILABLE but documentation-only** (`RISK-014`) |
| Indexed commit | Verified current at index time, 2026-08-05 |
| Queries to run | KG-Q-015 `detect_changes()` before each commit |
| Expected impact | New root files; no symbol dependencies exist yet |

## 20. Blast-radius assessment
Low reach (no consumers exist), high reversibility, but **confidence is limited** because the graph holds no application symbols. First `BR-001` is created with this step's first sub-step.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome | File |
| --- | --- | --- |
| STEP-001.01 | Workspace skeleton and pinned toolchain | [STEP-001.01](sub-steps/STEP-001/STEP-001.01-workspace-and-toolchain.md) |
| STEP-001.02 | Formatting, linting, strict TypeScript | [STEP-001.02](sub-steps/STEP-001/STEP-001.02-code-standards.md) |
| STEP-001.03 | Ownership and contribution governance | [STEP-001.03](sub-steps/STEP-001/STEP-001.03-ownership-and-governance.md) |
| STEP-001.04 | Local dependency stack | [STEP-001.04](sub-steps/STEP-001/STEP-001.04-local-dev-environment.md) |
| STEP-001.05 | Documentation and ADR-001 | [STEP-001.05](sub-steps/STEP-001/STEP-001.05-readme-and-adr.md) |
| STEP-001.06 | Knowledge-graph workflow wiring | [STEP-001.06](sub-steps/STEP-001/STEP-001.06-knowledge-graph-workflow.md) |

## 22. Test and evaluation plan
`TST-PLAT-001` (clean-checkout bootstrap), `TST-PLAT-002` (lock enforcement), `TST-PLAT-003` (ownership enforcement), `TST-PLAT-004` (ADR presence review).

## 23. Deployment, feature flag and migration plan
No deployment. No flags. No migration.

## 24. Rollback, compensation and recovery plan
Purely additive; revert by deleting the branch or reverting commits. No data or consumer impact.

## 25. Acceptance criteria
- [ ] A clean checkout runs lint, type-check, tests and the app from documented commands (`REQ-PLAT-001`)
- [ ] CI fails on an unlocked dependency change (`REQ-PLAT-002`)
- [ ] CI fails on a path with no owner (`REQ-PLAT-003`)
- [ ] `ADR-001` exists and is indexed in the decision log (`REQ-PLAT-004`)
- [ ] `CLAUDE.md` documents the GitNexus workflow and the no-AI-attribution commit rule
- [ ] `npx gitnexus status` reports the index current at `HEAD`

## 26. Evidence required for completion
| Evidence | Where recorded |
| --- | --- |
| Bootstrap run by an engineer who did not write it | Implementation log |
| CI failure screenshots for lock and ownership rules | Sub-step records |
| `npx gitnexus status` output | Sub-step 001.06 record |
| Regression R1–R7 | Regression log |

## 27. Open questions, risks and decisions
`BLK-001` no owners — blocks exit sign-off. `ASM-004` baseline versions need revalidation before pinning. Local Node is v25.9.0 while the target runtime is **Node 24 LTS** — the application runtime must be pinned regardless of the local version.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 6 |
| Commits / PR | — |
| Regression result | — |
| Post-change graph evidence | — |
| Verified by | — |
</content>
