---
sub_step_id: STEP-007.04
parent_step: STEP-007
title: Waitlist and inspiration mode with consent
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-002, REQ-PRIV-002, REQ-PRIV-004, REQ-PRIV-006]
blast_radius_id: BR-063
depends_on: [STEP-007.03]
last_updated: 2026-09-11
---

# STEP-007.04 — Waitlist and inspiration mode with consent

## 1. Outcome
Somebody outside coverage can ask to be told when it opens, having explicitly consented to being contacted for that purpose alone.

## 2. Scope and boundary
**In scope:** Waitlist capture; a purpose-specific consent record (`DATA-016`); inspiration content for uncovered regions.

**Not in this sub-step:** Email delivery (operations); account creation (`STEP-008`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-002, REQ-PRIV-002, REQ-PRIV-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date at `7a95fb6` before any edit |
| HEAD / indexed commit | `7a95fb6` / `7a95fb6` |
| Queries run | `impact(_problem_response, upstream)` — the one existing symbol modified. **1, LOW, `"epistemic": "exact"`, and grep agreed**: three call sites, all inside `check_planning`. Recorded because the last two records did not go this way; see `BR-063` §2, which also corrects `BR-061`'s over-strong claim that `app.py` has no outgoing edges. Everything else added here is new, and a new symbol has no dependants to under-report |
| Migration present? | **Yes — `019_waitlist.sql`.** `RISK-017` applies, so the blast radius came from running it against the deployed schema and from mutation: mutants 6, 7 and 9 are killed by CHECK constraints and by the partial index, not by application code |
| Unknown / low-confidence areas | Resolved before implementing, by **owner decision on three questions**: where pre-signup consent lives (`consent_records` cannot hold it), how withdrawal is exercised with no email delivery, and how far inspiration content goes. The recorded risk — "a beautiful page for a place we cannot plan may read as a promise" — was answered by keeping it text-only with the limitation stated first, and asserted by two tests |
| Blast radius | **`BR-063` — MEDIUM, confidence HIGH** |
| Approval required? | **Yes, and obtained.** Not from the score — MEDIUM would not have required it — but because all three open questions were privacy decisions on an unauthenticated surface that writes a stranger's personal data |

## 5. Implementation plan
- [x] Waitlist entry writes a consent record with **purpose `waitlist_notification` only** — **but not into `consent_records`; see §6**
- [x] Consent is independently withdrawable without affecting any other purpose (`REQ-PRIV-004`)
- [x] No pre-ticked boxes; consent is an action, not a default
- [x] Inspiration content clearly marked as not plannable yet
- [x] Email stored against the consent record, deletable on withdrawal (`REQ-PRIV-006`)

## 6. Contracts and schema changes

**The plan said "consumes the `ConsentRecord` shape from `DATA-016`". It cannot, and
that is the substance of this sub-step.**

`consent_records` is `organization_id NOT NULL, user_id NOT NULL` under forced
row-level security, and `STEP-008.04` owns it. A waitlist subject has no account, so
neither column has a value. The two ways to force a fit were to invent an
organization or to make the isolation columns nullable on the one table holding
consent so an unauthenticated endpoint could write to it — the first fabricates a
fact, the second aims at `R7`.

So `019_waitlist.sql` adds a platform-level `waitlist_entries`, for the reason `016`
moved coverage: an unauthenticated operation cannot touch tenant-scoped data, so
either the data is platform-level or the endpoint is wrong. `BUG-028` was this
collision on the read side. `BR-063` §3 carries the full reasoning and the owner
decision.

| Change | Classification |
| --- | --- |
| `db/migrations/019_waitlist.sql` | New table, no RLS — exempt from the isolation gate **by its own derivation rule**, having no `organization_id` column |
| `API-020` — `POST /waitlist`, `POST /waitlist:withdraw` | **`[ADDITIVE]` ×2** |
| `WaitlistConsent`, `WaitlistJoinRequest`, `WaitlistJoined`, `WaitlistWithdrawRequest`, `WaitlistWithdrawn` | New schemas, all closed |
| `ERROR_MODEL.md` | **Unchanged** — `validation.invalid_request` and `authz.forbidden` already existed and already said what was needed |

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PRIV-004 | integration | Withdrawing waitlist consent leaves other purposes intact |
| — | integration | **Withdrawal deletes the email**, traversing every store that holds it |
| — | browser | No consent control is pre-selected |
| — | unit | A waitlist entry without a consent record is refused |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
The waitlist email is personal data from the moment it is typed. It is never logged, never in a trace attribute and never in an event payload (`EVENT_CONTRACTS` §2).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()`; by inspection where a migration is involved |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert the commit and delete captured entries — the consent basis disappears with the feature, so retention would be unlawful.

## 12. Acceptance criteria
- [ ] Waitlist entry requires explicit, purpose-specific consent
- [ ] Withdrawal is independent and deletes the email
- [ ] No pre-ticked consent
- [ ] Inspiration content does not imply plannability

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-09-11 |
| Commit SHA | see git log for `STEP-007.04` |
| Pushed | see §14 |
| Graph re-indexed at | after commit, per the workflow loop |
| `main` green and deployable | ✅ `pnpm verify` exit 0 |
| Mutation testing | **13 seeded, 13 killed, 0 survivors** — `BR-063` §7 |
| Bugs found | **None.** Two of my own defects were caught by existing gates rather than shipped: a bare `403` (refused by `test_no_operation_declares_a_bare_403`) and a `possibly undefined` in a new test file (refused by the typecheck guard's meta-test, on the run where I had typechecked *before* writing it) |
| Notes / surprises | **Rolling this back is not just reverting code.** The consent basis for holding those emails is the feature itself, so a revert that leaves the rows behind converts a rollback into a retention problem. This is the first sub-step where the rollback plan has a legal component, and it will not be the last. |

### What the record should have said, and now does

The plan's central instruction — write a `ConsentRecord` — was not executable, and
finding that out was most of the work. The reconciliation that resolved it is worth
carrying forward, because `STEP-008.04` inherits it:

> **The grant is evidence and survives; the address is personal data and does not.**

`STEP-008.04` says withdrawal is a column and not a delete, because erasing the grant
destroys the evidence that processing was lawful. This sub-step says the email is
deletable on withdrawal. Both hold: a withdrawn row is a dated record that a lawful
grant existed, holding nothing that identifies anybody. It is a CHECK constraint
rather than a convention, so the mistake cannot be made quietly.

### The trade this sub-step ships with

Until an address is verified — which needs email delivery, out of scope here —
anybody who knows an address can rotate its withdrawal token and remove that entry.
The ceiling is removal from a notification list, and no personal data is disclosed.
It cannot be closed inside this scope: only the hash is stored, so a repeat join
cannot return the original token, and the alternatives were a membership oracle or no
withdrawal at all. Carried to email delivery.
