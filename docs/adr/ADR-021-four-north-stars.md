# ADR-021 — Four north stars gate Phase 1, with provisional values until the pilot baseline

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.

- **Date:** 2026-10-19 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- Closes `DEC-005` **on the question of north stars**. Proposed by the implementer at the
  owner's request; **confirmed final by the owner the same day.** Opens `DEC-013` for the
  engineering constants that had been citing `DEC-005` as their sign-off.

## Context

`DEC-005` has been open since 2026-08-05: Phase 1 had measures (`SUCCESS_METRICS` defines
nine KPIs) but no numbers, so its exit gates were not objectively evaluable. The register's
own constraint — and `SUCCESS_METRICS` §1 rule 5 — is that thresholds must come from
Phase 0/1 baselines, not be asserted in advance. Any decision here has to respect that
while still giving the pilot something to be designed against.

## Decision

Phase 1 is steered and gated by **four north stars**, all already defined in
`SUCCESS_METRICS`. Nothing new is invented. Each carries a **provisional pilot-design
value** and a guardrail. **Binding release gates are set from the first ~50 pilot briefs**,
once a baseline exists — until then the values below shape the pilot and are not gates.

| # | North star | Measures | Provisional value | Guardrail |
| --- | --- | --- | --- | --- |
| 1 | **Feasible choice** — `KPI-001` | Share of confirmed briefs yielding ≥3 valid, materially different scenarios | **≥ 80%** of Switzerland pilot briefs | Zero hidden hard-constraint violations (`KPI-002`, already blocking) |
| 2 | **Trust without re-verification** — `KPI-004` | Citation correctness on volatile facts; share of users rating evidence sufficient without external correction | Citation **≥ 95% — fixed**, already a release gate (blueprint §16.191). Trust rating **≥ 70%** provisional | Inaccuracies tracked separately, never netted against ratings |
| 3 | **Time to decision** — `KPI-003` | Median from confirmed brief to selected scenario | **≤ 50% of the Phase-0 manual-workflow median** — relative by design | Not achieved by hiding evidence or cutting diversity |
| 4 | **Stale-fact rate** — `KPI-002` (second half) | Facts past their freshness threshold ÷ facts used | **≤ 5%**, blocking above 10% | What makes north star 2 true operationally |

**Explicitly not north stars:** `KPI-006` booking handoff (externally gated on partners and
`ASM-012` — tracked, not steered by); `KPI-007` unit economics (a guardrail in Phase 1, not
a target — `ADR-019` just gave revenue two legs and a margin model does not exist yet);
`KPI-005`, `KPI-008`, `KPI-009` (Phase 3; nothing exists to measure).

## Options considered

| Option | Why not, or why |
| --- | --- |
| Set binding numbers now | Violates the register's own rule and §1 rule 5; a number asserted before measurement is a guess with a release gate attached |
| Leave everything unset until the pilot | The pilot then has nothing to be designed against, and "we'll know it when we see it" is how gates get negotiated downward after the fact |
| **Provisional values now, binding after baseline — chosen** | The pilot is designed against something concrete; the gate is set from evidence; the two are kept visibly distinct |
| More than four | Nine numbers is a dashboard, not a north star. Four is the smallest set that covers *did it work, can I trust it, was it fast, was it fresh* |

## Consequences

1. `SUCCESS_METRICS` threshold rows for `KPI-001`–`004` now carry the provisional values,
   marked provisional, with the baseline step named as the trigger that makes them binding.
2. **North star 3 cannot be evaluated until Phase 0 measures the manual workflow.** That
   measurement is now on the critical path to Phase 1 exit and did not previously exist as
   a task anywhere. Owed.
3. **`DEC-013` opens.** Every engineering constant that cited `DEC-005` — freshness classes
   (`STEP-005.08`), `MAX_ATTEMPTS` (`BR-055`), prune and replay limits (`BR-056`),
   `DRIFT_SIGMA` (`BR-057`), `RECOVERY_SUCCESSES` (`BR-049`), `ALERT_THRESHOLD` (`BR-048`),
   the diversity threshold (`STEP-011`), notification burden (`STEP-018`), replan thresholds
   (`STEP-019`) — now resolves to `DEC-013`. Those records are history and are not rewritten.
   Each constant's *invariant* is already tested; only its value awaits sign-off, which is
   exactly the state those records describe.
4. `KPI-007` stays a guardrail: quality, latency and diversity thresholds remain fixed during
   any cost optimisation. This ADR does not loosen that.
5. Phase 1 exit is now *evaluable in principle* — against provisional values today, against
   binding ones after the baseline.

## Affected knowledge-graph nodes

Documentation only: `SUCCESS_METRICS` §1, §2 (`KPI-001`–`004`), §5; `DECISION_LOG`
`DEC-005`, `DEC-013`; the open-decision rows in `MASTER_TRACKER`, `00-START-HERE`,
`OUT_OF_SCOPE`, `RELEASE_PLAN`, `RELEASE_READINESS_CHECKLIST`, `DEPENDENCY_REGISTER`,
`FUNCTIONAL_REQUIREMENTS`, `AI_ML_EVALUATION`. No code node — no metric is computed by any
code yet (`STEP-022`).

## Migration

None. Nothing computes these metrics today.

## Security and privacy implications

North star 2's trust rating is a survey response and a `user_reported_incorrect_fact`
event per trip — personal data under the existing consent model, nothing new. No metric
here may be improved through profiling (`REQ-PRIV-003`, §1 rule 3).

## Operational implications

`STEP-022` (analytics) must compute all four from the lineage `SUCCESS_METRICS` already
names, and must distinguish provisional from binding in whatever it renders. A dashboard
that shows a provisional value as a gate would be a defect.

## Tests

None today. `STEP-022` inherits: each north star computed from its declared lineage; the
guardrail for each breaches independently of the primary; a provisional threshold is never
rendered as a release gate.

## Rollback

Mark the four thresholds **Unset** again and reopen `DEC-005`. Nothing downstream has
consumed the values yet, so the cost is one document.

## Review trigger

The first pilot baseline exists (provisional → binding), or Phase 0 measures the manual
workflow (north star 3 becomes evaluable). Whichever comes first reopens this record for
the values, not for the choice of stars.
