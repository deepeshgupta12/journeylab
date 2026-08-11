---
blast_radius_id: BR-030
sub_step_id: STEP-004.03
title: Collaboration, booking, live and feedback operations (API-010…014)
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-030 — Collaboration, booking, live and feedback operations

> The sub-step record predicts `BR-024`, held by STEP-003.07. This is `BR-030`.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `dd01499` |
| HEAD at check | `dd01499` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** for impact; `gitnexus_query` remains unusable (`BR-029` §3) |
| Confidence | **HIGH** |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(safe_detail, upstream, includeTests)` | 2 impacted across 2 depths, **1 process**, LOW, `epistemic: exact` |
| 2 | `impact(ERROR_CODES)` | **Ambiguous** — the graph indexes the same symbol twice, once as `Property` and once as `Variable`, both at `error_codes.py:35`. Recorded in §3 |
| 3 | `detect_changes()` | Run pre-commit |

## 3. A fourth graph observation

`impact(ERROR_CODES)` returns `status: ambiguous` with two candidates that are
the same declaration at the same line, differentiated only by node kind
(`Property` and `Variable`). Both report 0 impacted, which is also wrong — the
constant is imported by `problem.py` and by two test modules.

Minor next to the JSX, CSS and FTS gaps, and recorded for the same reason: a
tool that answers confidently and wrongly is worse than one that declines. Added
to the `STEP-026` list.

## 4. Change inventory

| File | Change |
| --- | --- |
| `contracts/openapi.yaml` | **7 operations, 11 schemas.** API-010…014, with revoke and accept as separate operations |
| `tests/api/test_api_operations.py` | 29 new assertions |

No Python behaviour changed. No generated file regenerated — every error code
these operations reference was already registered.

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | Callers / call graph | None |
| 2 | **Public API / contracts** | 7 operations added, all `PROPOSED`. Purely additive |
| 3 | Database / schema | None. `DATA-013` (booking, segregated) and `DATA-015` (feedback) are referenced and undefined — STEP-006, as with `DATA-010/011` |
| 4 | Events | `EVT-004`/`006` referenced in prose; AsyncAPI is `.05` |
| 5 | Configuration | None |
| 6 | Infrastructure | None |
| 7 | **Security** | **The reason this is MEDIUM.** Three surfaces, all structural rather than procedural. See §6 |
| 8 | **Privacy** | `consent_scope` required on feedback; **no field can record the absence of feedback**; sentiment is explicit only (`REQ-PRIV-003`) |
| 9 | Accessibility | Not directly |
| 10 | Performance | None declared |
| 11 | Tenancy | Unchanged — still no operation accepts a tenant parameter |
| 12 | Documentation | This record, `IMPL-027`, the sub-step record, `REGRESSION_LOG`, `MASTER_TRACKER` |

## 6. Data-flow inspection

Nothing is implemented, so what is inspected is what the contract **permits**.

### 6.1 Payment credentials — the absence is the control

`TST-BOOK-002` asks that no schema permit a payment credential. It is asserted by
**scanning every property name in the document** against 21 payment-shaped names,
not by reviewing the booking schemas.

Review is what fails on the eighteenth operation added two years from now. And a
test that searches for something absent passes identically when the search is
broken — so a second test seeds `card_number` into a synthetic document and
requires the same walk to find it.

`BookingHandoff` is additionally a **closed** object, because an open one is
somewhere a credential can arrive undeclared.

**PCI scope you never enter is scope you cannot leak.** JourneyLab deep-links and
records attribution; it never sees a card.

### 6.2 Invitations — a link is a credential

| Hazard | Control |
| --- | --- |
| A link that outlives the collaboration | `expires_at` **required, no default** |
| An invitation conferring ownership | `role` enum excludes `trip_owner`. Transferring a trip is a deliberate act, not a forwardable link |
| A token retrievable after issue | Returned **once**, in the creation response. A test asserts no read operation can return `InvitationCreated` |
| Revocation that can be waited out | `DELETE` is immediate and irreversible; reissuing is cheap |

**A conflict worth recording rather than resolving here.** The register lists
`collaboration.invitation_expired` at **403**, described as "fail closed, leak
nothing". Those two are in tension: an attacker guessing invitation tokens learns
which guesses are real if "expired" is distinguishable from "never existed".

No operation in this sub-step returns it — redemption is not declared — so
nothing is wrong today. When the redemption endpoint is designed it must use the
indistinguishable denial, and the register's 403 will need revisiting. Flagged
for `.04` rather than changed now, because altering a security-relevant status
with no operation to test it against would be a change nothing exercises.

### 6.3 Feedback — consent, and the shape of silence

`consent_scope` is required, and the narrowest option is listed first so the
generated client's default ordering favours it.

**No field can record that feedback was not given.** The moment one exists,
something treats silence as dissatisfaction — and a traveller who simply got on
with their holiday is not an unhappy one. Asserted by name against five spellings
of the idea.

## 7. Repair generation is separate from acceptance — structurally

`REQ` aside, this is the design decision most likely to be undone by someone
optimising a round trip away.

`generateRepairs` returns options and changes nothing. `acceptRepair` is the only
operation in the contract that alters a live plan in response to a disruption.

The separation is enforced by their *shapes*: generation does **not** take
`If-Match` and acceptance does. Requiring a version precondition on a read-only
projection would imply it mutates, and the next person to touch it would make
that true.

A traveller mid-trip must be able to look at what a disruption costs without
committing. One operation that generated and applied would replan their afternoon
while they were still reading the first option.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Phase 2–3 steps implement against these |
| Reversibility | High | Declarative only |
| Detectability | High | 29 assertions, one of them meta-tested |
| Security exposure | Medium | Payment, invitation and consent surfaces fixed structurally |
| **Overall** | **MEDIUM** | Confidence HIGH |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **469 passed, 5 skipped** (up from 440) |
| `ruff` / mypy | Clean |
| Every `$ref` resolves; every example validates | Asserted |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
