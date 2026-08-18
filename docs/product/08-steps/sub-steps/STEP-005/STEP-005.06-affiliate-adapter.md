---
sub_step_id: STEP-005.06
parent_step: STEP-005
title: Affiliate deep-link generation and signed callback receipt
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-BOOK-001, REQ-BOOK-002]
blast_radius_id: BR-045
depends_on: [STEP-005.05]
last_updated: 2026-08-18
---

# STEP-005.06 — Affiliate deep-link generation and signed callback receipt

## 1. Outcome
Deep links preserve itinerary context where the provider permits, and attribution callbacks are verified before parsing — with **no payment credential anywhere**.

## 2. Scope and boundary
**In scope:** `services/integrations/src/affiliate/`; link generation; signed webhook receipt; replay-window enforcement; attribution records.

**Not in this sub-step:** Booking UI and reconciliation into itinerary items ([STEP-016](../../STEP-016-booking-handoff.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-BOOK-001, REQ-BOOK-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `5656b75` — matched HEAD at pre-change |
| Queries run | `cypher` over `services/integrations/src/affiliate` — 0 nodes, additive; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | **`EXT-005` still open — no partner selected**, and that is why `PartnerLinkProfile` records *observed* behaviour with a check date rather than assuming any. `ASM-012` is therefore **structurally testable but empirically unvalidated**: the shape to record an observation exists; no observation has been made. A claim without a check date is refused, so the gap cannot be filled with an assumption by accident |
| Blast radius | **[BR-045](../../../10-logs/blast-radius/BR-045-affiliate-adapter.md) — MEDIUM, confidence HIGH.** The record predicted `BR-035`, which STEP-004.08 holds; corrected here |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] Deep links carrying dates, party size and product id, from an **allowlist that contains nothing identifying** — a URL reaches browser history, referrer headers and the partner's logs
- [x] `PartnerLinkProfile` records observed preservation with a **required check date**; `UNVERIFIED` is distinct from `DROPPED`, and an undated claim is refused
- [x] **`verify_and_parse` takes raw bytes.** No function verifies a parsed object, and a test asserts the module's whole public surface so one cannot be added quietly
- [x] Both window edges enforced; duplicates inside the window accepted as already handled; the seen-set pruned so it cannot be a memory-exhaustion primitive
- [x] The verified callback is a **value**, not a side effect — the handler's only job is verify and hand off. Enqueueing is `STEP-006`'s transport
- [x] `AttributionRecord` is frozen, slotted and closed: no payment field exists to redact

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-BOOK-002 | security | No code path can persist a payment credential |
| — | security | Unsigned webhook discarded; replayed webhook outside window rejected |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [x] `BR-045`
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 925 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One package into `services/integrations/` |
| R4 untested requirements | **PASS — improved** | REQ-BOOK-001 and REQ-BOOK-002 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…026; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched; `AttributionRecord` requires a tenant |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Links preserve parameters per partner capability
- [ ] Signature verified before parsing
- [ ] Replay window enforced, duplicates idempotent
- [ ] No payment credential representable

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-18 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None in existing code. Two of my own, both caught before commit |
| Notes / surprises | **Verify before parse is an ordering, not a step**, and the natural way to write the handler gets it backwards: parse the body to find the signature, then verify — by which point a JSON parser has consumed attacker-controlled bytes, which is the whole surface the signature stood in front of. So the entry point takes raw bytes, and there is deliberately **no function that verifies a parsed object**, because that helper is the one everyone reaches for. A test asserts the module's entire public function set, since a new public function here is a new chance to reintroduce it.<br><br>**Replay protection and idempotency pull against each other.** One rejects OLD requests, the other accepts DUPLICATE ones, and §5 asks for both. Resolved by ordering rather than a special case: age is checked first, so a duplicate reaching the seen-set is inside the window by construction. Both edges matter — a future-dated callback is rejected too, or an attacker mints one valid for as long as they chose.<br><br>**"No payment credential anywhere" had to mean nowhere to put one.** Redaction runs after the value is in memory and one forgotten call from a log, so `AttributionRecord` is frozen, slotted and closed. And `reject_payment_fields` refuses rather than strips: a partner sending card data is a contract change to escalate, and filtering it silently means nobody finds out while the value still passes through our process.<br><br>**One mutant could not be killed behaviourally.** Replacing `hmac.compare_digest` with `!=` left everything green, correctly — a unit test cannot observe a timing side channel. Believed-to-hold and checked-by-nothing is the worst state for a security control, so the assertion moved into the source. Reported as **9 of 10 before that test existed and 10 of 10 after**; the sequence is the finding, and the final number alone would hide it.<br><br>**My own test caught my own regex.** The payment matcher missed `ccnum` — a name I had listed in the parametrised cases and then failed to cover. Naming the cases explicitly is what found it; trusting the pattern to be obviously complete would not have.<br><br>**`EXT-005` is still open and `ASM-012` remains empirically unvalidated.** No partner is selected, so no preservation has been observed. The design makes that state explicit rather than papering over it: `UNVERIFIED` is distinct from `DROPPED`, and a preservation claim without a check date is refused — an assumption cannot be entered as an observation by accident. |
