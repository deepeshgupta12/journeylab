---
blast_radius_id: BR-063
sub_step_id: STEP-007.04
title: Waitlist capture, purpose-specific consent and withdrawal
author: Deepesh Kumar Gupta
date: 2026-09-11
score: MEDIUM
confidence: HIGH
approval_required: true
---

# BR-063 — The waitlist, and where a stranger's consent lives

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `7a95fb6` |
| HEAD at check | `7a95fb6` |
| Freshness | ✅ `status` up to date before any edit |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** |

## 2. Queries run — and the graph was right this time

| Symbol | Graph (`upstream`) | Grep | Agreed? |
| --- | --- | --- | --- |
| `_problem_response` | **1, LOW, `"epistemic": "exact"`** | 3 call sites, all inside `check_planning` | ✅ |

Worth recording precisely because the last two records did not go this way.
`BR-061` §2 concluded that **`apps/api/src/app.py` has no outgoing edges at all**
and its handlers are island nodes. That is too strong: this query resolved a
`CALLS` edge inside `app.py` correctly, at `confidence: 0.85`.

The sharper statement, which both records now support: **intra-file edges in
`app.py` resolve; cross-file edges into it do not.** `BR-062` then showed the
under-reporting is not confined to `app.py` or to Python at all. `RISK-016` has
been widened accordingly.

Nothing else in this sub-step modifies an existing symbol. `join_waitlist`,
`withdraw_waitlist_consent`, the two handlers and the two components are new, and a
new symbol has no dependants to under-report.

## 3. The decision this sub-step forced, and why it went to the owner

The plan said *"Waitlist entry writes a `ConsentRecord`"*. It cannot.

`010_domain.sql` created `consent_records` (`DATA-016`) with `organization_id NOT
NULL`, `user_id NOT NULL`, `FORCE ROW LEVEL SECURITY` and a tenant-isolation policy.
Every one of those is correct for somebody with an account. **A waitlist subject has
no account**, so there is no organization to name and no user to reference.

| Option | Consequence |
| --- | --- |
| Invent an organization | Fabricates a fact that later readers will trust |
| Make the isolation columns nullable | Weakens the constraint `R7` protects, on the one table holding consent, so that an **unauthenticated** endpoint can write to it |
| **A platform-level table** | No tenant columns, because there is no tenant. `consent_records` and `R7` are untouched |

This is `BUG-028` one layer down: there, a public read met a tenant-scoped read model
and answered "we support nowhere"; here a public write meets a tenant-scoped consent
table. `016` settled the principle — an unauthenticated operation cannot touch
tenant-scoped data, so either the data is platform-level or the endpoint is wrong,
and the endpoint is the requirement.

**Owner approval was sought and given** for the table, for the withdrawal mechanism
and for the scope of inspiration content, because all three are privacy-affecting
decisions on an unauthenticated surface and none of them was settled by the plan.

`STEP-008.04` still owns `consent_records` and inherits the job of reconciling a
waitlist grant with a user's consent when the same person signs up. Named here
rather than discovered there.

## 4. Withdrawal: the two rules that sound contradictory

| Source | Rule |
| --- | --- |
| `STEP-008.04` | "Withdrawal is a column, not a delete — erasing the grant destroys the evidence that processing was lawful" |
| `STEP-007.04` | "Email stored against the consent record, **deletable on withdrawal**" |

They reconcile exactly: **the grant is evidence and survives; the address is personal
data and does not.** A withdrawn row records that a lawful grant existed and when it
ended, holding nothing that identifies anybody.

That is enforced by `waitlist_active_has_address`, a CHECK constraint, rather than by
the code remembering — so a future withdrawal path that cleared `withdrawn_at` and
forgot the address **fails to commit**. Mutants 6 and 7 confirm it.

## 5. The token, and the trade it makes

Email delivery is explicitly out of this sub-step, so there is nothing to send a
withdrawal link through. A 256-bit token is minted at capture and returned once; only
its SHA-256 is stored.

**The trade, stated rather than buried.** Until an address is verified — which needs
delivery — anybody who knows an address can rotate its token and withdraw that entry.
The ceiling is removal from a notification list; no personal data is disclosed,
because the response is byte-identical whether or not the address was already
present, which is also what stops this operation being a membership oracle.

It cannot be avoided within this sub-step's scope: only the hash is kept, so a repeat
join *cannot* return the original token, and the only alternatives were to respond
differently (a membership oracle) or not to return one at all (no withdrawal).
Recorded as a follow-up against verification, not left to be found.

## 6. Scoring

| Category | Assessment |
| --- | --- |
| Schema | **`019_waitlist.sql`** — new table, no RLS, `GRANT SELECT, INSERT, UPDATE` |
| Contract | **`API-020`** — two operations, both `security: []`, both `IdempotencyKey`. Compatibility gate: **`[ADDITIVE]` ×2** |
| Error model | **Unchanged** — `validation.invalid_request` and `authz.forbidden` already existed and already said what was needed |
| Code | `platform_api/waitlist.py` (new), two handlers, `_problem_response` gains `instance` and `status` |
| Web | `waitlist.tsx` (new), one line added to `coverage/page.tsx` |
| Security / tenancy | **No tenant path exists.** The RLS gate derives its set from the presence of an `organization_id` column, so this table is exempt **by the rule rather than by an exception** — which is what makes the exemption safe to leave |
| Personal data | **Yes, and it is the first of its kind here** — an unauthenticated write of a stranger's email |
| **Score** | **MEDIUM** |
| Approval | **Obtained** — three decisions put to the owner before implementation |

MEDIUM rather than HIGH: the surface is additive, nothing existing changes shape, and
the one modified symbol had a single caller. It is not LOW because it writes personal
data on an unauthenticated path, which is a category this repository had not had.

## 7. Mutation testing — 13 seeded, 13 killed

| # | Seeded defect | Rule it breaks |
| --- | --- | --- |
| 1 | `granted: false` accepted | an entry without consent is refused |
| 2 | any `purpose` accepted | purpose-specific consent (`REQ-PRIV-002`) |
| 3 | consent assumed at the call site | no entry on an assumed grant |
| 4 | the rejected address echoed in the message | the address is never echoed (`BUG-035`) |
| 5 | plaintext token stored | only the hash is stored |
| 6 | withdrawal keeps the address | `REQ-PRIV-006` |
| 7 | withdrawal clears one of the two columns | the address is gone from **every** column |
| 8 | a repeat join re-dates the consent | re-submitting a form is not a new decision |
| 9 | withdrawal re-dates on the second call | withdrawing twice changes nothing |
| 10 | `Idempotency-Key` not enforced | the declared parameter is required |
| 11 | an unknown token answers `403` | unknown and forbidden are indistinguishable |
| 12 | the consent box starts ticked | **no consent control is pre-selected** |
| 13 | an unconsented submit reaches the network | the address never leaves the browser |

Mutant 7 is the one that justifies its own test. Clearing `email` and leaving
`email_normalized` passes any assertion that checks the column somebody thought of,
and leaves a lower-cased, indexed, searchable copy of the address behind a withdrawal
nobody can inspect. It is killed by the constraint and by the whole-row assertion,
not by a column-specific one.

Mutant 12 can only be killed in a rendered document. A pre-ticked box is a property
of the first paint; every server-side test in this repository passes with it.

## 8. Follow-up created

| Item | Type |
| --- | --- |
| Address verification, so a token rotation cannot be requested by a stranger | Deferred to email delivery / `STEP-008` |
| Rate limiting on an unauthenticated write — `429` is declared in the contract and nothing enforces it | Deferred; no limiter exists yet |
| Reconciling a waitlist grant with `consent_records` when the subject signs up | `STEP-008.04` |
| `BR-061` §2's claim that `app.py` has no outgoing edges is too strong — intra-file edges resolve | Correction recorded here |
