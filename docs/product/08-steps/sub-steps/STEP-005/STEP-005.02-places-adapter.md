---
sub_step_id: STEP-005.02
parent_step: STEP-005
title: Places, hours and accessibility provider adapter
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-001, REQ-DATA-005]
blast_radius_id: BR-041
depends_on: [STEP-005.01]
last_updated: 2026-08-13
---

# STEP-005.02 — Places, hours and accessibility provider adapter

## 1. Outcome
Place entities, opening hours, closures, accessibility attributes and price ranges are ingested with full provenance and field-specific freshness.

## 2. Scope and boundary
**In scope:** `services/integrations/src/places/`; sanitized fixtures; licence record; hours parsing into intervals with time zones.

**Not in this sub-step:** Entity resolution (`.07`); freshness policy definition (`.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-001, REQ-DATA-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `9a82fa4` — matched HEAD at pre-change |
| Queries run | `cypher` over `services/integrations`; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | **This field's premise expired.** It says "No provider selected (EXT-001)" — written before `DEC-002` closed. `ADR-016` has since chosen Switzerland and named the sources, so this is built against **real licence terms**. What remains unverified is provider **payload shape**: no live fetch has been made, so field names are assumed and `.07` will meet the real ones |
| Blast radius | **[BR-041](../../../10-logs/blast-radius/BR-041-places-adapter.md) — MEDIUM, confidence HIGH.** The record predicted `BR-031`, which STEP-004.04 holds; corrected here |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] **Licence record required by signature** (`REQ-DATA-001`) — "before ingestion is enabled" is a sequencing claim, so it is kept by structure rather than by a check
- [x] Adapter mapping provider payload to a canonical place, **wider than the API's `Place`** so an internal field cannot become a public promise by accident
- [x] **Hours parsed into intervals with an explicit IANA zone**; a naive moment is refused and comparison happens after `astimezone`
- [x] Accessibility captured **as declared** — a closed vocabulary, unknown keys dropped with a warning, empty meaning *not declared*
- [x] Cases covered: success, absent hours, unparseable hours, unknown accessibility keys, missing zone, missing name, bad confidence
- [x] Provenance stamped with source, `observed_at`, confidence, access label **and `licence_id`** — the STEP-004.06 field that had no user until now

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-001 | CI | Ingestion refused without a licence record |
| TST-DATA-005 | unit | Seasonal hours produce correct effective windows |
| — | unit | Hours spanning midnight and DST parse correctly |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) `IMPL-038` · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · BUG_REGISTER n/a — no bug found
- [x] `BR-041`
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 772 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One package into `services/integrations/` |
| R4 untested requirements | **PASS — improved** | REQ-DATA-001, REQ-DATA-005 and REQ-PRIV-003's declared-only clause newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…025; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched; place data is public and not tenant-scoped |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Licence record exists and gates ingestion
- [x] Hours carry time zones and effective windows
- [x] Accessibility attributes never inferred
- [x] Fixtures cover all five cases

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | This adapter carries RISK-001 — no provider is identified. Everything here is buildable against fixtures, but cannot be validated until a contract exists. |
