---
blast_radius_id: BR-038
sub_step_id: STEP-005.01
title: Connector framework — credentials, egress, limits, circuit breaker
author: Deepesh Kumar Gupta
date: 2026-08-13
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-038 — Connector framework

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `ff28714` |
| HEAD at check | `ff28714` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — the change is additive into an empty namespace |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `cypher(MATCH n WHERE n.filePath STARTS WITH 'services/integrations')` | **0 nodes** — genuinely greenfield, so nothing existing can be broken |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

The sub-step record predicts `BR-030`, which STEP-004.03 holds. Corrected to
`BR-038` in the sub-step file.

## 3. The design decision the outcome depends on

§1 asks that "no adapter reimplements resilience". A **library of helpers** does
not achieve that — it achieves "no adapter *has to*", which is a weaker claim that
survives exactly until the first adapter written under deadline reaches for
`httpx` directly.

So `HttpConnector` owns the client and an adapter is handed a connector, never a
URL. There is no code path to an outbound request that skips the controls. That is
the difference between a framework and a toolbox, and it is why `connector.py`
composes rather than exports.

## 4. Why hostname allowlisting is not SSRF protection

The allowlist is the obvious control and it stops none of the three real cases:

| Bypass | What defeats it |
| --- | --- |
| **DNS rebinding** — resolves public at check time, private at connect time | Validate the **resolved address**, and check **every** address a host returns |
| **Redirect** — an allowlisted host answers 302 to `169.254.169.254` | Follow redirects **manually**, re-checking each hop |
| **A host that simply resolves inward** — a misconfigured record or a CNAME to an internal load balancer | Same address check; no hostility required |

`169.254.169.254` is the target that matters: AWS, GCP and Azure all serve instance
credentials there to anything inside the VPC that can make a plain GET. `DEC-007`
has not chosen a provider and it does not need to — all three are blocked, along
with `fd00:ec2::254` and the IPv4-mapped form `::ffff:169.254.169.254`, which is
neither `is_private` nor `is_link_local` by the standard library's predicates while
resolving to exactly the address being blocked.

## 5. Change inventory

**Added** — `services/integrations/src/framework/`: `egress.py`, `resilience.py`,
`schema_gate.py`, `checkpoint.py`, `credentials.py`, `connector.py`; and
`tests/integrations/test_connector_framework.py` (62 assertions).

**Modified** — `pyproject.toml` (`services/integrations/src` on the path,
`types-jsonschema`, two test-scoped lint ignores).

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None. Nothing imports the framework yet; adapters are `.02`–`.06` |
| 2 | **Public API / contracts** | None. The compatibility gate confirms no diff |
| 3 | **Database / schema** | None. `CheckpointStore` is a **port**, so `STEP-006` still owns canonical persistence rather than inheriting a table decided here |
| 4 | **Events** | None. Provider health events are `.06` |
| 5 | **Configuration** | Egress allowlist, rate limit, quota and TTL are per-connector construction arguments, not globals |
| 6 | **Infrastructure** | No new runtime dependency — `httpx` and `jsonschema` were already present |
| 7 | **Security** | **The substance of the sub-step.** SSRF, egress, mandatory timeouts, and a credential type that cannot be logged |
| 8 | **Privacy** | `Secret` has no readable `__str__`, `__repr__` or `__format__`. The commonest way a credential reaches a log is an f-string in an error path |
| 9 | **Accessibility** | None — no user-facing surface |
| 10 | **Performance** | One DNS resolution per call. Deliberate: caching it re-opens the rebinding window |
| 11 | **Tenancy** | Untouched. Connectors fetch public timetables and hold no tenant data |
| 12 | **Documentation** | This record, `IMPL-035`, the regression entry, the sub-step, parent §21, `MASTER_TRACKER` |

## 7. Mandatory data-flow inspection

**Flow:** adapter → connector → breaker → quota → limiter → egress check → request
→ redirect? re-check → schema gate → checkpoint.

| Hazard | Control | Evidence |
| --- | --- | --- |
| Reaching cloud instance metadata | Resolved-address check against 12 IPv4 and 6 IPv6 ranges | 13 parametrised cases; seeded removal killed by 3 |
| A redirect escaping the allowlist | Manual redirect handling, re-checked per hop | Seeded; killed by 3 |
| DNS ordering deciding the verdict | **All** resolved addresses checked | Seeded `addresses[:1]`; killed |
| An unbounded request | `timeout_seconds <= 0` raises at construction | Tested |
| Stale data served during an outage | `CircuitOpenError` carries no payload — there is no channel to return one | Tested on the type, not just behaviour |
| A recovered provider knocked over again | Half-open admits exactly one probe | Seeded; killed |
| A provider's value silently becoming ours | The schema gate returns the **identical object** or raises | Asserted with `is`; seeded coercion killed by 3 |
| A provider redesign treated as a bad row | `SchemaDriftError` is distinct and catchable as a rejection | Tested |
| Duplicated records after a crash | Commit ordering enforced by the API — there is no method that advances the cursor without claiming work | Tested, including the crash-before-commit case |
| A resume silently restarting | An empty cursor cannot be committed | Seeded; killed |
| A credential surviving rotation | TTL cache plus `invalidate()` on 401 | Tested both |
| A credential in a log line | `Secret` refuses to render in `str`, `repr` and f-strings | Tested all three |
| An egress denial tripping the breaker for a healthy provider | `EgressDeniedError` re-raised before the failure handler | Tested |

## 8. What went wrong while building it

**A sentinel that was also a legal value.** `TokenBucket._last` and
`Quota._window_start` used `0.0` for "not yet initialised", and the tests inject a
clock starting at `0.0` — so the first refill computed zero elapsed time and three
tests failed on the first run. Both are `None` now. The lesson is not about clocks:
*a sentinel drawn from the value's own domain is a bug waiting for its first
legitimate caller*, and injected time makes that caller arrive immediately.

**A mutant survived, and it mattered.** Flipping the production client to
`follow_redirects=True` left all 61 tests green, because every test injects its own
client and the constructor's default was never exercised. That is not cosmetic:
`httpx` would follow the redirect internally and return the final response, so hop
two would never reach `egress.check_url` and the metadata bypass would be open with
every redirect test still passing. Closed by asserting the constructor default
directly — white-box, because a constructor default has nowhere else to be observed.

## 9. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every provider adapter in `.02`–`.06` is built on this |
| Reversibility | High | A new package; nothing imports it yet |
| Detectability | High | 62 assertions, 8 mutants seeded, 8 killed |
| Security exposure | **Medium — reducing** | Establishes the SSRF and egress controls `REQ-SEC-005` requires |
| Performance | Low | One resolution per call, deliberately uncached |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 10. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **727 passed, 5 skipped** (up from 665) |
| Mutation | 8 seeded, 8 killed — one only after closing the gap it exposed (§8) |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
