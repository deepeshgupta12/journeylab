---
blast_radius_id: BR-065
sub_step_id: BUG-036
title: Waitlist retention — until sent, never more than 12 calendar months
author: Deepesh Kumar Gupta
date: 2026-09-14
score: MEDIUM
confidence: HIGH
approval_required: true
---

# BR-065 — Waitlist retention

Not a sub-step. The fix for `BUG-036`, found while gathering `STEP-007`'s exit evidence
and done before the step closes because it is a gap in shipped personal-data handling.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `345b593` |
| HEAD at check | `345b593` |
| Freshness | ✅ `status` up to date before any edit |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH — from grep, the live migration and the tests, not the graph** |

## 2. Queries run — `RISK-016` #16 and #17

| Symbol | Graph (`upstream`) | Grep | Agreed? |
| --- | --- | --- | --- |
| `join_waitlist` | **0, LOW, `"epistemic": "exact"`** | the handler in `apps/api/src/app.py` + 15 test references | ❌ |
| `withdraw_waitlist_consent` | **0, LOW, `"epistemic": "exact"`** | the handler in `apps/api/src/app.py` + 9 test references | ❌ |

Three for three, across `BR-064` and here, on **cross-file calls into the API
application**. Neither function's body changed in this fix — retention was added
beside them — but both are named because the widened CHECK constrains the rows they
write.

## 3. What changes, by category

| Category | Change |
| --- | --- |
| Schema | **`020_waitlist_retention.sql`** — `notified_at`, `expired_at`, two new CHECKs, a partial index, and `waitlist_active_has_address` recreated under the same name with a wider meaning. `RISK-017` applies: the graph holds one node per `.sql` file |
| Code | `platform_api/waitlist.py` — `RETENTION_MONTHS`, `months_before`, `RetentionSweep`, `expire_waitlist_entries`. **No existing function body modified** |
| Contract | `joinWaitlist` description states the period — **description only**, compatibility gate green |
| Web | The consent text on the form states the period |
| Error model | Unchanged |
| Tenancy | None — `waitlist_entries` has no tenant column (`BR-063` §3) |
| Personal data | **Yes** — this is a retention rule for a store of email addresses |

## 4. The widened constraint was proven safe against real rows

`waitlist_active_has_address` was dropped and re-added in one transaction against the
dev database, which held rows from every earlier waitlist test run — active and
withdrawn. **It added without error.** Every active row has an address and no
`expired_at`; every withdrawn row has neither, so both satisfy the widened rule. Checked
by running the migration, not by reasoning about it.

## 5. The cutoff is computed in Python, in UTC

`timestamptz - interval '12 months'` is evaluated in the session's `TimeZone`, so the
same entry could be due on one connection and not another. `months_before` computes
the cutoff once, in UTC, with the day clamped — 12 months before 29 February 2028 is
28 February 2027. No date library was added: a new dependency is its own blast radius,
and the arithmetic is eight lines and tested at both month ends and across a leap year.

## 6. Scoring

| | |
| --- | --- |
| **Score** | **MEDIUM** — a schema change on a table of personal data, with no existing function body modified |
| **Confidence** | HIGH |
| **Approval** | **Obtained** — `DEC-012`, owner decision as privacy owner, before implementation |

## 7. Mutation testing

**14 seeded, 14 killed** — two of them only after fixing what the first run exposed.

| # | Seeded defect | Killed by |
| --- | --- | --- |
| 1 | cutoff computed as `now - 365 days` | the leap-year sweep test (`TestTheSweepCountsCalendarMonths`) |
| 2 | the 12-month boundary made exclusive | `test_a_grant_exactly_twelve_months_old_has_ended` |
| 3 | sending does not end the entry | `test_a_notified_entry_ends_however_young_it_is` |
| 4 | withdrawn entries swept too | `test_withdrawn_entries_are_left_alone` |
| 5 | expiry keeps the address | the whole-row assertion + the CHECK |
| 6 | expiry clears `email` and not `email_normalized` | the whole-row assertion + the CHECK |
| 7 | an entry can expire before it was granted | `test_an_entry_granted_after_the_sweep_instant_is_not_touched` |
| 8 | a second sweep re-ends rows | `test_a_second_sweep_ends_nothing_the_first_ended` |
| 9 | the day not clamped | `test_a_leap_day_clamps_to_the_end_of_february` |
| 10 | month arithmetic in local time, not UTC | `test_a_zoned_instant_is_converted_to_utc_first` — **after that test was rewritten** |
| 11 | a naive instant accepted | `test_a_naive_instant_is_refused` |
| 12 | `RETENTION_MONTHS` changed to 24 | the pin test |
| 13 | the form stops stating the period | the component test |
| 14 | **the live CHECK reverted to `019`'s** (schema mutant, `RISK-017`) | `test_the_schema_refuses_an_expired_row_that_kept_its_address`, plus every sweep test, since the sweep cannot null an address under the old rule |

Every kill is counted against a **green baseline under the identical invocation**, checked
before the first mutant and again after the last.

**Mutant 10 survived the first run, and it was the test's fault.** The "zoned instant"
test used 00:30 on 1 January in Zurich. Subtracting twelve months in local time and
comparing instants lands on exactly the same instant as doing it in UTC, so deleting the
conversion changed nothing the test could see — while its docstring claimed it would land
on a different day. Local and UTC arithmetic only diverge when the two calendars disagree
about a day that gets clamped: 00:30 on 29 February 2028 in Zurich is still the 28th in UTC.
The test now uses that instant, and the mutant dies on it alone.

**Mutant 14's first restore failed, and that was the script's fault.** It nulled the
addresses on expired rows *before* swapping the constraint back — so the still-installed
mutant CHECK rejected the repair and the transaction rolled back, leaving the **weaker
constraint live** in the dev database. The script said so (`REAL CONSTRAINT NOT RESTORED`)
rather than carrying on. Restored by hand in the right order — drop, repair, add — with one
row repaired: the expired row the mutant had let keep its address. The rerun used the
correct order, and `convalidated` was confirmed true afterwards.

## 8. Follow-up created

| Item | Type |
| --- | --- |
| **Nothing runs `expire_waitlist_entries`.** No scheduler exists in the repository; retention is enforceable and tested, and not enforced | Deployment (`STEP-027`) |
| Nothing sets `notified_at`: there is no sender, so today only the 12-month cap can end an entry | Email delivery |
| `RISK-016` #16, #17 | Risk register |
