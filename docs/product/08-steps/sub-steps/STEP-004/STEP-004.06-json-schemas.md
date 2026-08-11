---
sub_step_id: STEP-004.06
parent_step: STEP-004
title: Shared JSON Schemas including model-output schemas
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005, REQ-AI-002]
blast_radius_id: BR-033
depends_on: [STEP-004.05]
last_updated: 2026-08-11
---

# STEP-004.06 — Shared JSON Schemas including model-output schemas

## 1. Outcome
Request, response, event and **model-output** shapes share one schema library, so the deterministic boundary around AI output is contractual.

## 2. Scope and boundary
**In scope:** `contracts/jsonschema/`; shared types (money, temporal validity, provenance, constraint classes); model-output schemas for `AI-001`.

**Not in this sub-step:** Prompt content ([STEP-009](../../STEP-009-trip-brief-and-structured-constraints.md)); retrieval configuration.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005, REQ-AI-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date at `e1d3194` |
| HEAD / indexed commit | `e1d3194` / `e1d3194` — matched |
| Queries run | `detect_changes()`. No symbol-level query applicable — five JSON documents, one YAML refactor, no Python symbol changed |
| Unknown / low-confidence areas | **One found during the work:** §5's "no duplicate inline definitions" makes this a **refactor**, not an addition. `Money` and the provenance/time fields were already inline in `openapi.yaml`, so adding the library without moving them would have created the duplication the sub-step forbids (`BR-033` §3) |
| Blast radius | **[BR-033](../../../10-logs/blast-radius/BR-033-json-schema-library.md) — MEDIUM, confidence HIGH.** The record predicted `BR-027`; taken by the STEP-003 closure |
| Approval required? | **No** |

## 5. Implementation plan
- [x] Shared `Money`, `TemporalValidity`, `Provenance` — and `Evidenced` in the OpenAPI document **recomposed** from the latter two rather than restating them
- [x] `ConstraintClass` with the four values kept distinct, and the schema states what collapsing each pair would break
- [x] Model-output schema for TripBrief extraction — per-field class and confidence, **plus a required `source_span`** that makes a hallucination deterministically detectable
- [x] `$id` versioning under `/v1/`, unique, matching filenames, with cross-references absolute
- [x] Reuse enforced — the gate searches for the **shape** (`amount_minor` + `currency`), not the name, because a duplicate would never be called `Money2`

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-AI-002 | contract | Model output violating the schema is rejected | ✅ 8 rejection cases: version, class, span, confidence, extra fields, missing required |
| — | CI | No duplicated inline type where a shared schema exists | ✅ **by shape, not by name**, with the scan meta-tested |
| — | contract | Abstention is expressible and required — `REQ-AI-004` | ✅ |
| — | contract | The schema states that it checks shape, not truth | ✅ a reader who believes otherwise skips the two gates after it |

40 assertions. Python suite: 552 → **592**.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-027` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 592 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS — on timing** | `Evidenced` changed its required set; no consumer exists yet. After `.07` the same change is breaking |
| R3 graph diff as expected | **PASS** | Five JSON documents, one YAML refactor |
| R4 untested requirements | **PASS — improved** | REQ-AI-002 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** **PASS**. Detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] One schema library shared by request, response, event and model-output shapes
- [x] Model-output schema makes the deterministic boundary contractual — 8 rejection cases
- [x] `$id` versioning in place and asserted
- [x] Reuse enforced by a gate that searches for shape rather than name

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None. Two tests broke correctly on the refactor, **and one of them would have gone vacuous rather than red** had I only added the library — see the regression entry |
| Notes / surprises | **This sub-step is a refactor and the plan does not say so.** "Reuse enforced — no duplicate inline definitions" reads like an addition; in fact `Money` and the provenance/time fields were already inline in `openapi.yaml` from `.01` and `.02`, so creating the library without moving them would have produced exactly the duplication being forbidden.<br><br>**One broken test would have gone vacuous instead of red.** It read `schemas["Money"]["properties"]` — and after a bare `$ref` there are no `properties`, so it would have iterated an empty set and passed. The gate that searches for the *shape* of a duplicate rather than its name is what makes the library real.<br><br>**R2 passes on timing, not on design.** `Evidenced` changed its required set, which is harmless today and breaking the moment `.07` generates a client. Doing this before client generation rather than after was the difference between a refactor and a migration.<br><br>The most valuable field in the model-output schema is `source_span`. A model claiming the traveller is "travelling with a dog" must point at the characters that say so — which is the only defence against a fluent hallucination nobody actively disbelieves. |
