---
blast_radius_id: BR-045
sub_step_id: STEP-005.06
title: Deep links, signed callbacks and attribution
author: Deepesh Kumar Gupta
date: 2026-08-18
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-045 — Affiliate adapter

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `5656b75` |
| HEAD at check | `5656b75` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — additive; nothing imports it yet |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `cypher` over `services/integrations/src/affiliate` | 0 nodes — additive |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

## 3. Verify before parse is an ordering, not a step

§5: *"Verify webhook signature before parsing the body."*

Almost every implementation gets this backwards, and it does not look backwards:

```python
body = json.loads(request.body)      # the parser has now run
verify(body["signature"], body)      # on unauthenticated input
```

By the time the signature is checked, a JSON parser has consumed
attacker-controlled bytes — which is the entire surface the signature was meant to
stand in front of.

So the entry point takes **raw bytes** and returns a parsed payload only after the
HMAC matches, and there is deliberately **no function that verifies against a
parsed object**. Such a helper is what everyone would reach for, and reaching for
it is the bug, so it does not exist to be reached for. A test asserts the module's
public function set, because a new public function here is a new chance to
reintroduce it.

Two consequences follow and are recorded at the code:

- **The signature is over the exact bytes received.** Re-serialising a parsed body
  produces different bytes and breaks the signature; implementations that hit this
  usually "fix" it by canonicalising, which quietly restores parse-before-verify.
- **The timestamp is inside the signed material.** A replay window checked against
  a timestamp the attacker can edit is not a window, so `verify_and_parse` takes it
  as an argument rather than reading it from a payload it has not yet trusted.

## 4. Replay protection and idempotency pull in opposite directions

§5 asks for both, and they conflict: replay protection rejects requests that are
**old**, idempotency accepts requests that are **duplicate**. A partner retrying
after a timeout sends the same event again, legitimately, and must not be treated
as an attack.

Resolved by ordering: `verify_and_parse` rejects on age first, so a duplicate that
reaches `SeenEvents` is inside the window by construction and is reported as
already handled rather than refused. The seen-set is pruned to the window, because
an unbounded one is a memory-exhaustion primitive for anyone able to send signed
callbacks.

Both edges of the window are enforced. A **future-dated** callback is rejected too
— without that, an attacker mints a request that stays valid for as long as they
chose, which is a window with no far edge.

## 5. "No payment credential anywhere" means nowhere to put one

`TST-BOOK-002`: *"No code path can persist a payment credential."*

A redaction pass cannot satisfy that — it runs after the value is in memory and one
forgotten call from a log. `AttributionRecord` is a closed, slotted, frozen set of
fields with no `payment_method`, no `card_last_four`, no `billing_address`: not
redacted, **absent**. The same argument as `service_identities` in migration 001,
which has no secret column at all.

`reject_payment_fields` **refuses rather than strips**, at any depth and inside
lists. A partner that starts sending card data has changed the contract, and
filtering it silently means nobody finds out — while the value still passes through
our process and possibly our logs on the way to being dropped. The matcher works on
the *shape* of a field name rather than an exact list, because an exact list is one
somebody must keep complete forever.

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None yet. Booking UI and reconciliation are `STEP-016` |
| 2 | **Public API / contracts** | None. `BookingHandoff` already exists in `openapi.yaml`; nothing changed |
| 3 | **Database / schema** | None. Persistence is `STEP-006` — and `AttributionRecord`'s shape is what a table must not exceed |
| 4 | **Events** | None. Async enqueue is declared here as an obligation, wired in `STEP-006` |
| 5 | **Configuration** | The shared secret is a parameter; no default, no module constant |
| 6 | **Infrastructure** | None. `hmac` and `hashlib` are stdlib |
| 7 | **Security** | **The substance of the sub-step.** Verify-before-parse, constant-time comparison, both window edges, bounded seen-set |
| 8 | **Privacy** | `REQ-PRIV`: no payment data can be stored; the deep-link allowlist carries nothing identifying, because a URL reaches browser history, referrer headers and the partner's logs |
| 9 | **Accessibility** | None directly. `unreliable_parameters` exists so an interface can warn rather than imply the context carried over |
| 10 | **Performance** | One HMAC per callback |
| 11 | **Tenancy** | `tenant_id` required on every attribution record; a row without one cannot be isolated or deleted |
| 12 | **Documentation** | This record, `IMPL-044`, the regression entry, the sub-step, parent §21, `MASTER_TRACKER` |

## 7. Mandatory data-flow inspection

| Hazard | Control | Evidence |
| --- | --- | --- |
| A parser run on unauthenticated bytes | Entry point takes `bytes`; no verify-a-parsed-body function exists | Seeded an early parse; killed by 2. Public function set asserted |
| A signature guessed byte by byte | `hmac.compare_digest` | **Structurally asserted** — §8 |
| A captured request replayed tomorrow | Age checked before any cryptography | Seeded; killed |
| A request minted to stay valid indefinitely | Future edge enforced | Seeded; killed |
| A timestamp edited to refresh a replay | Timestamp inside the signed material | Seeded; killed |
| A legitimate retry treated as an attack | Duplicates inside the window accepted as already handled | Tested |
| Memory exhausted by signed traffic | Seen-set pruned to the window | Seeded; killed |
| An attacker learning why a callback failed | One exception type, one message | Seeded a distinct message; killed |
| A card number reaching storage | No field exists; frozen and slotted | Assignment refused; `__slots__` asserted |
| A card number reaching a log en route to being dropped | Refused, not stripped, at any depth and inside lists | Seeded both; killed by 15 and 1 |
| A traveller identified from a deep link | Parameter allowlist carries nothing identifying | Asserted |
| A handoff rewritten in transit | `https` required | Asserted |
| An unverified preservation claim read as verified | `UNVERIFIED` is distinct from `PRESERVED`, and a claim needs a check date | Seeded; killed by 2 |

## 8. The mutant that could not be killed behaviourally, and what was done about it

Replacing `hmac.compare_digest` with `!=` left the whole suite passing — correctly,
because a unit test cannot observe a timing side channel.

That is the worst possible state for a security property: everyone believes it
holds and nothing checks it. So the check moved to where the property lives, and a
test now asserts `hmac.compare_digest` appears in `verify_and_parse` and that plain
equality against the signature does not. With that in place the mutant dies.

Same technique as `.05`'s assertion that no haversine helper exists: **when
behaviour cannot see a property, the source can.** Reported as 10 of 10 killed
*after* the structural test was added, and 9 of 10 before it — the sequence matters
more than the final number.

## 9. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every booking handoff and callback flows through these |
| Reversibility | High | A new package; nothing imports it |
| Detectability | High | 44 assertions, 10 mutants, 10 killed |
| Security exposure | **Medium — reducing** | Establishes the callback-verification discipline `REQ-BOOK-002` needs |
| Performance | None | One HMAC per callback |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 10. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **925 passed, 5 skipped** (up from 881) |
| Mutation | 10 seeded, 10 killed — one only after being made structurally checkable |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
