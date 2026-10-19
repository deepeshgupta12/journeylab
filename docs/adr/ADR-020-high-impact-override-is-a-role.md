# ADR-020 — Approving a high-impact fact override is a role, held today by the owner alone

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.

- **Date:** 2026-10-19 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- Closes `DEC-010`. **Owner directive** ("it will be RBAC — currently I will control the
  same"), recorded by the implementer the same day.
- **This ADR records the decision and does not implement it.** See *Consequences* §1.

## Context

`AUTHORIZATION_MATRIX` row *Approve high-impact override* (`API-016`) grants `curator` a
conditional `⚠️ second curator` and `ops_admin` a bare `⚠️📋` with **no named condition**.
The matrix is executable: `tools/gen_authz_matrix.py` generates `apps/api/src/authz/matrix.py`
from it, and the generator refuses a conditional it cannot resolve. That refusal is how
`DEC-010` was found at `STEP-002.03`, which encoded the cell **fail-closed**: today no
`ops_admin` can approve a high-impact override at all.

`DEC-010` offered two options — (a) change the cell to `❌`; (b) name the condition and
write it into §4 — and blocked `STEP-021`.

## Decision

**Option (b), expressed as role-based access control.** Approval of a high-impact fact
override is an explicit, grantable capability — a role, provisionally named
`override_approver` (the name is fixed at `STEP-021`, not here) — and **not** a property
of being `ops_admin`. The `ops_admin` cell's condition becomes: *holds `override_approver`*.

**Today the only holder is the owner.** The four-eyes rule is unchanged: the approver may
never be the actor (`REQ-ADMIN-002`). One consequence is stated rather than hidden: with a
single holder, **an override the owner makes themselves cannot be approved by anyone.**
That is the `ADR-010` one-owner gap appearing in a new place, and it is accepted on the
same terms.

## Options considered

| Option | Why not, or why |
| --- | --- |
| (a) `❌` — `ops_admin` can never approve | Simplest, but leaves the platform with exactly one approval path (a second curator) and no way to act when no second curator exists — which is the current state |
| Any `ops_admin` may approve | Rejected: a blanket admin capability violates §4's *service identity* rule and least privilege. "Admin" is not a reason |
| **(b) a named, grantable role — chosen** | Least privilege, auditable grants, and the capability can be given to a second human the day one exists without redesign |

## Consequences

1. **The matrix cell is not edited by this ADR.** Editing a cell changes system behaviour
   (the matrix's own header says so), which makes it a code change under rule 1 — it needs
   its own impact record and the full regression gate. `DEC-010`'s row already places the
   implementation at `STEP-021`. **Fail-closed stays live until then**, which is the safe
   direction to be wrong in.
2. **`STEP-021` must deliver:** the role and its grant/revoke mechanism (owner-granted,
   every grant and revoke an audited event); the §4 rule text naming the condition; the
   regenerated `authz/matrix.py`; and an extension of `TST-ADMIN-002`.
3. Granting the role is itself a high-privilege action. When a second human exists it
   should be four-eyes'd like the override it enables; until then it is single-actor and
   audited, like everything else under `ADR-010`.

## Affected knowledge-graph nodes

Named for `STEP-021`'s blast-radius record, **unchanged today**:
`apps/api/src/authz/matrix.py` (`approve_high_impact_override`), `authz.policy`,
`tests/api/test_authorization_matrix_sync.py`, `tests/api/test_authz_policy.py`
(`TST-ADMIN-002`), `AUTHORIZATION_MATRIX` §3 row and §4 *Four-eyes* rule.

## Migration

None today. At `STEP-021`: the role table and the owner's initial grant are an
expand-phase migration; no existing row changes meaning.

## Security and privacy implications

Least privilege is preserved — the capability is narrower than `ops_admin`, not wider.
No personal data is involved in the role itself; the override it enables touches
destination facts only (curator isolation, §4).

## Operational implications

None until `STEP-021`. After it: a runbook entry for granting and revoking the role, and
an alert on any grant, since each one widens who can change a fact travellers rely on.

## Tests

At `STEP-021`, at minimum: a holder can approve *another* actor's override; a holder
cannot approve their own; a non-holder `ops_admin` is denied with the standard problem
document (no bare 403); every grant and revoke appears in the audit log.

## Rollback

Revoke the role from all holders. The cell then behaves exactly as it does today:
fail-closed.

## Review trigger

Either of: a second person joins the project (`BLK-001`'s gap closes and the grant should
become four-eyes'd), or `STEP-021` begins.
