---
blast_radius_id: BR-066
sub_step_id: BUG-037
title: A region that lost a provider could never recover — and the dedupe key that would lose a second outage
author: Deepesh Kumar Gupta
date: 2026-09-16
score: MEDIUM
confidence: HIGH
approval_required: true
---

# BR-066 — Coverage recovery and the `EVT-008` dedupe key

Not a sub-step. The fix for `BUG-037`, found while designing the degradation drill
`STEP-007` §22 requires, and done before the step closes because `STEP-007.05` wired
the defective fold to the table a traveller reads.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `69ff50d` |
| HEAD at check | `69ff50d` |
| Freshness | ✅ `status` up to date before any edit |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** |

## 2. Queries run — the graph was right once, wrong once, and HIGH once

| Symbol | Graph (`upstream`) | Grep | Agreed? |
| --- | --- | --- | --- |
| `fold_coverage` | 1, LOW — one test | `coverage_projection` + 2 test references | ✅ in substance: its only production reach is through `coverage_projection` |
| `coverage_projection` | **19, HIGH** | 17 in `test_projections.py`, 4 in `test_read_models.py`, 4 in `test_degradation_disclosure.py` — **all tests** | ✅ — **the first time in six records the graph found the full set** |
| `HealthChanged` | 1, LOW — a test import | `provider_health.py`, 3 test references, 1 docstring mention | ✅ |
| `HealthChanged.dedupe_key` | **0, LOW, `"epistemic": "exact"`** | **1 test** — `test_the_dedupe_key_matches_the_contract` | ❌ — **`RISK-016` #18**, a property read from a test module |

**The HIGH verdict is recorded and warned on, and it does not set the score.** Every
one of the 19 dependants is a test. There is no production caller of
`coverage_projection`: `STEP-007.05` built `apply_coverage_state` as a seam and no
`EVT-008` consumer runs it. The reach is test churn, not runtime.

## 3. The two decisions, and who took them

| Decision | Options | Taken by |
| --- | --- | --- |
| How the fold remembers providers | per-provider state in the fold · the same keyed by HMAC · severity counters from `previous_state` | **Implementer, on the owner's instruction to choose** — per-provider state |
| The dedupe-key finding | log and carry to deployment · fix the contract now | **Owner** — fix now |

**Why per-provider state.** `EVT-008` declares `x-journeylab-replay: "Safe — state is
absolute, not incremental."` Counters derived from `previous_state` are incremental by
construction, and one missed or deduplicated event would leave a count wrong until a
full rebuild. The HMAC variant keys a small, known provider set, so it is reversible by
trying each name: it protects against reading, not against anyone who wants the
answer, and adds a secret to manage for that.

**What it costs.** The rule narrows from "provider identity never enters the
projection state" to **"never persisted and never published"**. That is the rule
`REQ-EVID-006` and the AsyncAPI description actually state — `provider_id` "never
leaves the platform" — and the old, stricter reading was the defect: a fold that cannot
remember a provider cannot let the provider recover. Both identity tests were
re-pointed at where persisting happens, and one now also asserts the fold **does** hold
the provider, so the narrowing is explicit rather than silent.

## 4. A second hole the fix found in itself

The first version of the new fold applied a provider's state to the regions its event
listed **plus** every region the provider was already known in. An existing test caught
the consequence: a provider that stops serving a region would keep degrading it for
ever — `BUG-037` again, reached through a configuration change.

So `affected_regions`, when present, is treated as the provider's **complete** set, and
the provider is released from any region it no longer lists. When absent — it is
optional in the contract — the new state applies wherever the provider is known, so a
recovery that names no regions still clears what its outage degraded.

## 5. The dedupe key

`x-journeylab-dedupe-key: provider_id + new_state` dedupes on the state **value**. A
provider that goes down, recovers and goes down again emits two events with the same
key, so a broker honouring the declaration would discard the second outage, and the
projection would show a provider healthy while it was down.

A transition-shaped key, `provider_id + previous_state + new_state`, fails the same way:
the second outage repeats the first transition exactly. Only an occurrence identity
distinguishes a redelivery from a new outage, and `event_id` is the one
`EVENT_CONTRACTS` §3 rule 1 already requires every consumer to dedupe by. **This
repository's code was never exposed** — `IdempotentConsumer` dedupes by `event_id` — so
the defect was in the contract a broker would be configured from.

## 6. Scoring

| Category | Change |
| --- | --- |
| Code | `services/events/src/projections.py` — `fold_coverage` rewritten, `_region_row` added. `services/ingestion/src/provider_health.py` — `dedupe_key` property removed, one error message |
| Contract | `contracts/asyncapi.yaml` — `EVT-008` `x-journeylab-dedupe-key` → `event_id`. **Not compatibility-gated: see §7** |
| Schema | None |
| Docs | `EVENT_CONTRACTS.md` `EVT-008` delivery row |
| Tests | Recovery tests, delivery tests, two identity tests re-pointed, one round-trip test given distinct providers, one dedupe test rewritten |
| Tenancy | None |
| **Score** | **MEDIUM** — a behaviour change on a projection with no production caller yet, and a contract extension on an internal stream with no consumer outside this repository |

## 7. R2 has no gate for this change, stated rather than implied

`tests/guards/contract-compatibility.sh` runs `tools/check_compatibility.py`, which diffs
**OpenAPI only**. `contracts/baseline/` includes `asyncapi.yaml` and its digest is
checked, but nothing compares the live AsyncAPI document against it. So "R2 PASS" for
this change would be a claim no tool made.

What was checked instead, by hand: the `EVT-008` payload schema is unchanged
(`provider_id`, `previous_state`, `new_state`, `reason` required; `affected_regions`
optional), no delivery mode or order key changed, and the baseline snapshot was not
edited, so its digest still matches. `BASELINE.md` records the baseline as
**pre-release, released to no consumer**, which is why changing a dedupe declaration
now is cheap — and why it would not be later.

## 8. Mutation testing

**11 seeded, 11 killed, 0 survivors** — against a green baseline checked before the
first mutant and again after the last, each killed by the test written for it.

| # | Seeded defect | First killer |
| --- | --- | --- |
| 1 | a region with no provider affecting it is `stale` | `test_a_provider_that_stops_listing_a_region_is_released_from_it` |
| 2 | a provider is never released from a region it stopped listing | same |
| 3 | a recovery naming no regions reaches nothing | `test_a_recovery_that_names_no_regions_clears_what_its_outage_degraded` |
| 4 | the first state a provider reports sticks | `test_a_provider_that_recovers_releases_its_region` |
| 5 | severity ordering is wrong | `test_one_recovery_does_not_mask_a_sibling_still_down` |
| 6 | every region accepts trips | `test_a_region_takes_its_worst_provider` |
| 7 | an unreadable state folds as `current` | `test_an_unreadable_state_folds_as_stale_not_as_current` |
| 8 | provider identity is ignored again — the original defect | `test_one_recovery_does_not_mask_a_sibling_still_down` |
| 9 | the provider map is written to the database | `test_no_provider_identity_reaches_the_read_model` |
| 10 | the dedupe key goes back to `provider_id + new_state` | `test_evt008_dedupes_by_event_id` |
| 11 | a payload-level `dedupe_key` returns | `test_a_second_outage_is_a_second_event_not_a_repeat_of_the_first` |

Mutant 8 is the one that matters: it restores the original defect exactly — the fold
ignoring `provider_id` — and it dies on a recovery test that did not exist before this
fix. Mutants 9 and 11 guard the two rules the fix narrowed rather than removed.

## 9. Follow-up created

| Item | Type |
| --- | --- |
| **AsyncAPI has no compatibility gate** — a breaking event-contract change would pass `pnpm verify` | Tooling gap, carried to the step that promotes a baseline |
| `RISK-016` #18 | Risk register |
| Nothing converts `HealthChanged` into an `EVT-008` envelope in production, so `previous_state` has never been carried end to end | `ENH-007` |
