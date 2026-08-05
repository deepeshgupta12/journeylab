---
step_id: STEP-027
title: Release automation and controlled rollout
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-004, STEP-023]
requirement_ids: [REQ-PLAT-009, REQ-PLAT-010, REQ-PLAT-011, REQ-PLAT-012, REQ-SEC-009, REQ-KG-004]
api_ids: []
event_ids: []
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-027 — Release automation and controlled rollout

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A single release gate spans software, data, ML and GenAI quality. Releases ship as reversible increments with automated canary and rollback, and migrations stay backward compatible through the rollout window.

## 2. Why this step exists
Every quality commitment in this documentation set is aspirational until something blocks a release that violates it. This step is where the gates become mechanical rather than cultural.

## 3. Scope
Test and evaluation harness; verify workflow with all gates; infrastructure modules and environments; deployment manifests; expand/migrate/contract migration plans; feature, model, provider and cohort flags; signed builds with provenance, staged rollout, smoke tests and rollback.

## 4. Explicit exclusions
Individual test suites are written in the steps that produce the code they cover; dashboards and alerts are [STEP-024](STEP-024-observability-sre-and-support-readiness.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| SRE | Deploy, rollback (audited) | Infrastructure | Internal |
| CI identity | Build, sign, deploy | Artifacts | Internal |
| Release manager | Cut release, sign off | Release evidence | Internal |

**No production personal data in staging or CI** — synthetic or de-identified only.

## 6. Preconditions and dependencies
[STEP-004](STEP-004-contract-first-platform-apis.md) contracts; [STEP-023](STEP-023-security-privacy-and-compliance-controls.md) security controls. **Blocked on `DEC-007`** (cloud provider and region).

## 7. Inputs and source systems
Test suites, evaluation datasets, scorers, IaC, environment configuration, flag definitions.

## 8. Detailed normal workflow
1. Merge triggers the verify workflow: lint, types, unit, contract, security, data quality, accessibility, AI evaluations.
2. **Change-impact record presence is checked** — a missing record blocks the merge.
3. Signed artifacts with provenance are built.
4. Staging deploy runs smoke tests and drills.
5. Canary at 5%, held against SLO and quality gates, then 50%, then 100%.
6. Graph is re-indexed at the release commit and an **immutable release graph is tagged**.
7. Any gate breach triggers automated rollback.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Any gate regresses | **Release blocked** | Not shipped | REQ-PLAT-009 |
| Missing change-impact record | Merge blocked | Not merged | REQ-KG-008 |
| Canary abort condition met | **Automated rollback**, no human judgement under pressure | Prior version restored | REQ-PLAT-010 |
| Migration not backward compatible | Blocked before deploy | Not shipped | REQ-PLAT-011 |
| Unsigned artifact | Cannot deploy | Blocked | REQ-SEC-009 |
| Model regression | **Model rolled back independently of the application** | App unaffected | REQ-PLAT-012 |

## 10. State machine and lifecycle transitions
`merged → verified → staged → canary 5% → 50% → 100% → released`, with `→ rolled back` reachable from every stage after staging.

## 11. Frontend implementation
Frontend builds, bundle budgets and accessibility checks run inside the verify workflow; no dedicated UI.

## 12. Backend implementation
`tests/{unit,integration,e2e,evals,contracts,security,resilience}/`, `mlflow/scorers/`, `.github/workflows/{verify,deploy}.yml`, `infra/{modules,environments}/`, `deploy/{helm,migrations,flags}/` (all `PROPOSED`).

## 13. API, event and integration contracts
Enforces [CONTRACT_CHANGE_POLICY](../04-contracts/CONTRACT_CHANGE_POLICY.md) in CI: compatibility diff, client regeneration, no hand edits, deprecation metadata.

## 14. Data model, migration and retention effects
Owns migration execution policy: **expand/migrate/contract**, backward compatible throughout the rollout window, with the contract phase gated on graph confirmation that no reader remains.

## 15. AI, LLM, RAG, ML and data-science implementation
Runs AI evaluation gates on gold and adversarial sets; enforces cost/latency budgets; verifies the **non-AI fallback works** at every promotion; supports independent model/prompt rollout and rollback. Human-aligned scorers live in `mlflow/scorers/`.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-SUPPLY-01/02` SBOM, signing, scanning; policy-as-code for network, admission, artifact and IAM; **accessibility checks are a release gate, not a report**; no production personal data outside production.

## 17. Observability, analytics and KPIs
Pipeline duration, gate failure rate by category, canary abort frequency, rollback frequency and MTTR, deployment frequency. A rising gate-failure rate in one category signals where quality is eroding.

## 18. Files and modules expected to change
All `PROPOSED` — see §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` for application code — static fallback |
| Queries to run | KG-Q-008 governance sweep as a release gate |
| Expected impact | CI changes affect every subsequent change's safety |

## 20. Blast-radius assessment
A defect in the gates themselves is the highest-leverage failure in the repository: it silently permits every other defect. Changes to the verify workflow require owner approval and a demonstration that a seeded regression is still caught.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-027.01 | Test harness and tiered execution (fast / full / release) |
| STEP-027.02 | Verify workflow with all gates |
| STEP-027.03 | Change-impact record enforcement (`TST-KG-008`) |
| STEP-027.04 | AI evaluation gates and scorers |
| STEP-027.05 | Signed builds with provenance and SBOM |
| STEP-027.06 | Infrastructure modules and environments |
| STEP-027.07 | Deployment manifests and migration plans |
| STEP-027.08 | Flag configuration for feature, model, provider, cohort |
| STEP-027.09 | Canary with automated abort conditions |
| STEP-027.10 | Automated rollback exercised in staging |
| STEP-027.11 | Release graph tagging |

## 22. Test and evaluation plan
`TST-PLAT-009` … `TST-PLAT-012`, `TST-SEC-009`, `TST-KG-004`. **Meta-test:** seed a deliberate regression in each gate category and prove the release is blocked. A gate never tested against a real failure is a gate nobody trusts.

## 23. Deployment, feature flag and migration plan
This step **is** the deployment plan. Staging must be production-like or the gate is theatre.

## 24. Rollback, compensation and recovery plan
Automated rollback exercised in staging before production use. Model, data and application rollbacks are independent. Contract-phase migrations are the one irreversible action and are gated accordingly.

## 25. Acceptance criteria
- [ ] Release blocked by regression in contracts, security, accessibility, data quality, model performance or business guardrails (`REQ-PLAT-009`)
- [ ] Automated rollback exercised in staging (`REQ-PLAT-010`)
- [ ] Migrations remain backward compatible through the rollout window (`REQ-PLAT-011`)
- [ ] Feature, model, provider and cohort flags change behavior without deployment (`REQ-PLAT-012`)
- [ ] Unsigned artifacts cannot deploy; SBOM produced (`REQ-SEC-009`)
- [ ] Immutable release graph tagged at the release commit (`REQ-KG-004`)

## 26. Evidence required for completion
Seeded-regression results per gate category; rollback exercise record; migration rehearsal; canary abort test; signed artifact verification; release graph tag.

## 27. Open questions, risks and decisions
`DEC-007` cloud provider and region — **blocking**. Canary cohort sizing needs traffic projections that do not exist (`ASM-002`). Fast-tier test budget must be set once suite duration is measurable.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 11 |
| Regression result | — |
| Verified by | — |
