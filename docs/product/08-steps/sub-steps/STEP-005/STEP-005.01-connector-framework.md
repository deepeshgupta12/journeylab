---
sub_step_id: STEP-005.01
parent_step: STEP-005
title: Connector framework: credentials, egress, limits, circuit breaker
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002, REQ-DATA-003, REQ-SEC-005]
blast_radius_id: BR-038
depends_on: [STEP-004.08]
last_updated: 2026-08-13
---

# STEP-005.01 — Connector framework: credentials, egress, limits, circuit breaker

## 1. Outcome
One framework provides credential rotation, egress allowlisting, rate limiting, quota budgets, checkpointing, schema validation and circuit breaking, so no adapter reimplements resilience.

## 2. Scope and boundary
**In scope:** `services/integrations/src/framework/`; secret-manager integration; SSRF protection; retry with capped backoff and jitter; circuit-breaker state machine.

**Not in this sub-step:** Individual provider adapters (`.02`–`.06`); entity resolution (`.07`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002, REQ-DATA-003, REQ-SEC-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `ff28714` — matched HEAD at pre-change |
| Queries run | `cypher` for nodes under `services/integrations` — **0**, genuinely greenfield; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | **The §4 question — does the secret manager support rotation without restart — is still unanswerable**, because `DEC-007` has not chosen one. What is settled is the shape that makes rotation possible: a one-method port, a TTL cache, `invalidate()` on 401, and no module-level constant. That shape does not change with the vendor |
| Blast radius | **[BR-038](../../../10-logs/blast-radius/BR-038-connector-framework.md) — MEDIUM, confidence HIGH.** The record predicted `BR-030`, which STEP-004.03 holds; corrected here |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] Credential retrieval behind a port, TTL cache, `invalidate()` on 401. `Secret` cannot be rendered by `str`, `repr` or an f-string
- [x] **Egress allowlist and SSRF protection** on every call **and every redirect hop** — resolved addresses, not hostnames
- [x] Per-provider token bucket and quota, as **distinct** errors because the remedies differ
- [x] Timeout on every request — `timeout_seconds <= 0` raises at construction, so there is no way to configure an unbounded call
- [x] Capped exponential backoff with **full** jitter, then circuit break
- [x] Checkpoint persistence behind a port, with the commit ordering enforced by the API
- [x] Schema gate that **rejects, never coerces** — returns the identical object or raises

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-SEC-005 | security | Non-allowlisted egress blocked; SSRF payload rejected |
| TST-DATA-003 | resilience | Repeated failures trip the breaker; recovery is half-open |
| TST-DATA-002 | integration | Checkpoint resumes without duplication |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) `IMPL-035` · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · BUG_REGISTER n/a — no bug found
- [x] `BR-038`
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 727 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One package into an empty namespace |
| R4 untested requirements | **PASS — improved** | REQ-SEC-005, REQ-DATA-002, REQ-DATA-003 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…024; meta-suite 61/61 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] All framework capabilities implemented and composed so none can be bypassed
- [x] Egress allowlist enforced — **on resolved addresses and on every redirect hop**
- [x] Circuit breaker trips, half-opens with a single probe, and reopens on a failed probe
- [x] Schema drift is a distinct error from a bad record, catchable as either
- [x] Checkpoint resume proven not to duplicate — including the crash-before-commit case

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-13 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None in existing code. Two of my own, caught before commit — see below |
| Notes / surprises | **A toolbox would not have met the outcome.** "No adapter reimplements resilience" is not achieved by helpers, which achieve "no adapter *has to*" — a weaker claim that lasts until the first adapter written under deadline imports `httpx` directly. So the connector owns the client and an adapter is handed a connector, never a URL.<br><br>**Hostname allowlisting is not SSRF protection**, and this was the main design finding. It stops none of the three real cases: DNS rebinding, a redirect from an allowlisted host, and a host that simply resolves inward through a misconfigured record. All three pass a name check. So the check is on the resolved address, on every address a host returns, on every redirect hop. `169.254.169.254` is the target that matters and `DEC-007` need not be decided for that — AWS, GCP and Azure all serve credentials there.<br><br>**A mutant survived, and it was a real hole.** `follow_redirects=True` on the production client left all 61 tests green, because every test injects its own client and the constructor default was never exercised. `httpx` would have followed the redirect internally and returned the final response, so hop two would never reach the egress check. More test cases would not have found this — the gap was in what the suite *touched*, not in what it asserted.<br><br>**A sentinel drawn from the value's own domain.** `0.0` meant "not initialised" for the token bucket and quota window, and the injected clock starts at `0.0`. Three failures on the first run, which is the good outcome: injected time makes that class of bug arrive immediately instead of in production.<br><br>**`gitnexus_rename` could not be used for the exception renames**, and that is worth recording rather than quietly working around: the index predates these files, so the graph has no nodes for them. The rule still holds for indexed symbols.<br><br>**The §4 question remains unanswerable.** Whether the secret manager rotates without a restart depends on `DEC-007`. What is settled is the shape that makes rotation possible at all, and that shape does not change with the vendor. |
