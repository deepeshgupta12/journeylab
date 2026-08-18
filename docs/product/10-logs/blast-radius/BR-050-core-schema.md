---
blast_radius_id: BR-050
sub_step_id: STEP-006.01
title: Canonical core schema, RLS, immutability and booking segregation
author: Deepesh Kumar Gupta
date: 2026-08-18
score: HIGH
confidence: MEDIUM
approval_required: true
---

# BR-050 — Core schema

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `c346697` |
| HEAD at check | `c346697` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED — and see §2, because "not blocked" overstates it** |
| Confidence | **MEDIUM** |

## 2. The pre-change check has nothing to say about a migration

| # | Query | Graph | Grep |
| --- | --- | --- | --- |
| 1 | `impact bind_tenant --upstream` | 0, LOW | **27** |
| 2 | `impact app_current_org --upstream` | 0, **UNKNOWN** | 6 |
| 3 | `impact RequestContext --upstream` | 5, LOW | **63** |
| 4 | `cypher` — nodes in `*.sql` | **one node per file** | — |

Query 4 is the finding. Every migration in this repository is **a single node**: no
tables, no columns, no constraints, no policies, no grants. `app_current_org` is a
SQL function, which is why it comes back `UNKNOWN` rather than with dependants.

So for the change type this step's own §20 calls *"low reversibility — a destructive
migration cannot be undone by reverting code"*, the mandated knowledge-graph
pre-check contributes **nothing beyond confirming the file exists**. `REQ-KG-008`
makes that check a release gate; here it is a formality.

This is distinct from `RISK-016` (which under-reports Python dependants) and worse
in one specific way: `RISK-016` gives a wrong number, and a wrong number can be
cross-checked. This gives no answer at all about the object being changed, and the
protocol has no step that notices. Logged as **`RISK-017`**.

**What was done instead.** The blast radius below is derived from grep, from the
migration itself, and from eleven mutations applied to the **deployed schema** (§7)
— because for a schema the question "is the guarantee live" is answerable only by
asking the database.

## 3. Approval, and the gap in it

§20: *"Every schema sub-step requires expand/contract and owner approval."* Score is
HIGH, so approval is required.

With a single owner the author is also the approver — the `ADR-010` four-eyes gap,
in force here exactly as it was on `BR-008`, the previous highest-risk change.
**Stated, not glossed.** The owner directed this step; that is authority to proceed
and it is not a second pair of eyes.

## 4. What changed

| Category | Assessment |
| --- | --- |
| Code | None. `db/migrations/010_domain.sql` is new; one line added to the R7 script (§8) |
| Schema | **15 new tables, 1 new schema, 2 new roles, 13 RLS policies, 3 immutability triggers** |
| Public API contract | Untouched |
| Events | None — the outbox is `.06` |
| Security | **The main surface.** Tenant isolation, role segregation, immutability |
| Privacy | Retention is a column and deliberately not a policy — §6 |
| Reversibility | **Expand phase only.** No existing table is altered, so a revert drops new objects and leaves 001–003 exactly as they were |

## 5. Immutable is not undeletable, and the distinction is the design

`TripBrief`, `EvidencePack` and `ScenarioVersion` reject `UPDATE` at the database.
`REQ-CONS-006` makes a scenario reproducible from its inputs; if an input can be
edited afterwards, "reproducible" means "reproduces whatever it says now", which is
not a property anybody can rely on. A comment saying *do not update* is not a
constraint.

**`DELETE` stays permitted, on purpose.** `REQ-PRIV-006` requires deletion to
traverse primary, object, vector, graph, cache, export and token stores. A table that
could not be deleted from would make the right to erasure unimplementable — **a
privacy defect manufactured by a reproducibility control.** Blocking `UPDATE` alone
is what keeps both requirements true at once, and a test asserts the deletion half
rather than only the refusal.

Enforced twice, because each half covers what the other cannot: the revoked grant
stops `journeylab_app`, and the trigger stops everyone **including the migration
owner**, which is the account a well-meaning data fix would use.

## 6. Retention is a column, not a policy

§27: *"Retention defaults per entity need the privacy owner's approval."* They have
not been given, so `trips.retention_days` is nullable and **NULL means undecided,
not unlimited** — the same distinction `LicenceRecord.max_cache_seconds` draws for
cache duration.

Picking a default would be inventing a privacy policy and giving it the authority of
a schema default, which is `BUG-026`'s shape in a place where it would be much
harder to notice. No automatic deletion runs against these tables in this sub-step.

## 7. Mutating the schema, because mutating the file proves nothing

The migration is `CREATE ... IF NOT EXISTS`, so re-applying a mutated file leaves the
existing schema untouched and every test passes. The question that matters is whether
the guarantee is **live in the database**, so each mutant weakens the deployed schema,
runs the tests, and restores — the same construction as the R7 meta-test.

**11 seeded, 11 killed**: trigger dropped, `UPDATE` granted, `FORCE` removed, policy
widened to `USING (true)`, planning role given the booking schema, booking role given
a planning table, two lineage columns made nullable, Null Island check dropped, a
`card_number` column added, money completeness dropped.

**The restore step found its own defect.** A mutant that lets a *write* through leaves
the row behind, and the row then blocks its own restore — dropping the Null Island
check let a `0,0` place be inserted, and re-adding the constraint failed against it.
The suite reported `11/11 killed` and `SCHEMA NOT RESTORED` in the same breath. Only
the final verification step caught it; without that line the run would have looked
like a clean pass while leaving the database weakened. Cleanup is now part of the
restore, and the verification stays.

## 8. A derived check is only as complete as the schema in front of it

`test_tenant_isolation.sh` derives its FORCE-RLS assertion from the catalogue rather
than a hardcoded list — deliberately, so a new tenant table is covered by whoever
creates it. But the script applies only migrations 001 and 003, so on a standalone
run the thirteen new tables would not exist, the derived query would find nothing to
complain about, and **the assertion would pass having checked tables that were not
there**.

Derivation removes the risk of an out-of-date list; it does not remove the risk of an
incomplete schema. 010 is now applied by the script.

## 9. What this does not close

| Gap | Why |
| --- | --- |
| Domain-specific payloads are `jsonb` | The itinerary DAG is STEP-011's design, ranking features are STEP-012's. Modelling them now would be inventing another step's schema; each has a `schema_version` beside it so the owning step adds structure by expand migration |
| No repository or model reads these tables | `.03` and `.04` |
| Retention is unset | §6, awaiting the privacy owner |
| `evidence_pack_facts` carries `organization_id` redundantly | Denormalised on purpose: RLS needs the column on the row it protects, and a join-based policy would be a per-row subquery |
| Contract-phase migrations | None exist yet. Nothing has been dropped or renamed, so the irreversible phase has not started |

## 10. Score

Fifteen tables, an eight-step fan-out, and a change type that cannot be undone by
reverting code. **HIGH**, confidence MEDIUM — the graph cannot see the object being
changed (§2), so confidence rests on the mutation results rather than on the
mandated check. Owner approval required and recorded in §3 with its gap.
