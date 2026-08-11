---
blast_radius_id: BR-032
sub_step_id: STEP-004.05
title: AsyncAPI event contracts with delivery guarantees (EVT-001…008)
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-032 — AsyncAPI event contracts

> The sub-step record predicts `BR-026`, held by STEP-003.09. This is `BR-032`.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `d2f950b` |
| HEAD at check | `d2f950b` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** in the change. The tooling caveats from `BR-031` §3 stand |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `detect_changes()` | Run pre-commit |
| 2 | — | **No symbol-level query was applicable.** This sub-step adds one YAML document and one test module and changes no Python symbol. Running an impact query to produce a number would be theatre |

Recording "no applicable query" explicitly rather than running an irrelevant one
and reporting LOW. The protocol asks for a pre-change check, not for a query.

## 3. The confirmation the sub-step asked for

§4 of the sub-step: *"DEC-009 (queue vs Kafka) does not change the contract, only
the transport — confirm that holds."*

**It holds, and it is now enforced.** The document declares no `servers` block
and no channel `bindings` — the two places AsyncAPI lets a transport leak into a
contract. `x-journeylab-delivery` states the guarantee a transport must *provide*,
which is what a consumer actually depends on. A test asserts both absences, so
answering DEC-009 later cannot quietly bind the contract to the answer.

## 4. Change inventory

| File | Change |
| --- | --- |
| `contracts/asyncapi.yaml` | **New.** 8 events, shared envelope, explicit guarantees |
| `tests/api/test_event_contracts.py` | **New.** 60 assertions |

No Python behaviour changed. No generated file regenerated.

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | Callers / call graph | None |
| 2 | **Public API / contracts** | A second contract document. Additive; `openapi.yaml` untouched |
| 3 | Database / schema | None. The outbox is STEP-006 |
| 4 | **Events** | **This is the change.** All 8 declared with envelope, payload, partition key, delivery guarantee, retention and replay safety |
| 5 | Configuration | None |
| 6 | Infrastructure | None — deliberately. No transport is named (§3) |
| 7 | **Security** | **The payload rule is a tenancy control, not a privacy nicety.** See §6 |
| 8 | **Privacy** | `EVT-007` outlives the data it describes and carries a **pseudonymous** subject reference. Failure reasons are codes, not prose |
| 9 | Accessibility | None |
| 10 | Performance | None |
| 11 | **Tenancy** | `tenant_id` required on every envelope (`REQ-SEC-001`); STEP-006's outbox is specified to refuse an unstamped one |
| 12 | Documentation | This record, `IMPL-029`, the sub-step record, `REGRESSION_LOG`, `MASTER_TRACKER` |

## 6. Data-flow inspection

### 6.1 Why "no content in payloads" is a tenancy control

`EVENT_CONTRACTS.md` §1 requires payloads to carry "IDs, versions and
classifications" and never trip content, evidence prose, personal data or precise
location. That reads like a privacy preference. It is not.

**An event is read by consumers that never authenticated the user who caused
it.** `EVT-001` alone goes to evidence assembly, the knowledge graph and
analytics. A payload carrying constraint values hands all three data nobody
checked they may see — and the check cannot be retrofitted, because the data is
already in the log and in every replica of it.

Payloads carry IDs. A consumer needing content reads it back through an
authorized API, where the tenant boundary is applied on every request.

Asserted by scanning every payload property against 24 content-shaped names —
personal data, coordinates, and the prose fields — for all eight events, plus a
meta-test proving the scan finds a seeded `accessibility_needs`. Every payload is
additionally **closed**.

`EVT-001` is the clearest case: a constraint is the traveller's own words about
their accessibility needs, their budget and who they travel with. The event
carries **four integers**.

### 6.2 The deletion event outlives what it describes

`EVT-007` is the proof artifact for `REQ-PRIV-006`, retained for a legally
required minimum — longer than the data it records the destruction of.

So `subject_ref` is **pseudonymous**, and a test asserts no `user_id` or `email`
appears. A proof of deletion that carries the person's identity defeats the act it
proves.

Failure reasons are `reason_code`, not free text: a reason written as prose
eventually contains the row it failed on. And failure **emits** with
`status: failed` rather than staying silent — silence is indistinguishable from a
crashed producer, and `REQ-PRIV-007` requires the failure to be visible and
queued.

### 6.3 Provider identity is internal, and the two shapes differ on purpose

`EVT-008` carries `provider_id`. That is correct: it is an internal stream driving
the coverage refusal path.

The public coverage endpoint publishes **one aggregate health value** precisely
because this event's contents must not reach a client. A test asserts no
client-adjacent event names a provider, so the two shapes cannot converge by
someone copying a payload.

## 7. The delivery guarantees, and the one that is usually stated wrongly

| Guarantee | Events | Why |
| --- | --- | --- |
| `at-least-once` | EVT-001, 002, 003 | A duplicate is wasteful, not damaging — an idempotent pack build or a re-recorded generation |
| `exactly-once-effect` | EVT-004, 006, 007 | A duplicate does real damage: a second booking handoff, a repair applied twice, a corrupted audit trail |
| `deduplicated-stream` | EVT-005, 008 | High-volume signals where the dedupe key is the contract |

**`exactly-once-effect`, not `exactly-once`.** No transport gives exactly-once
delivery; anything claiming to is deduplicating somewhere and calling it a
guarantee. What is required is that the *effect* happens once, which is the
consumer's obligation — so the contract names the obligation instead of implying
the transport will absorb it. A test asserts the description says so.

Two events are **not** keyed by `trip_id`: a deletion request spans every trip a
subject has, and provider health is not a property of a trip at all. Keying either
by `trip_id` would be a partition choice that looks consistent and is wrong.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | STEP-006's outbox and every consumer step implement against this |
| Reversibility | High | One new document; nothing depends on it yet |
| Detectability | High | 60 assertions, one meta-tested |
| Security exposure | Medium | The payload rule is the tenancy boundary for the whole stream |
| **Overall** | **MEDIUM** | Confidence HIGH |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **552 passed, 5 skipped** (up from 492) |
| `ruff` / mypy | Clean, 34 source files |
| No transport bound; no content in any payload | Asserted |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
