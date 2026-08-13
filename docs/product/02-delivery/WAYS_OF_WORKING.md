# JourneyLab — Ways of Working

> Governance that was not explicitly requested but is required for the sub-step workflow to function: branching, review, definition of ready/done, escalation and agent conduct.

| Field | Value |
| --- | --- |
| Owner | TPM (Deepesh Kumar Gupta) |
| Status | `READY` |
| Last reviewed | 2026-08-05 |

Navigation: [Sub-step protocol](SUB_STEP_PROTOCOL.md) · [Change impact protocol](../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md) · [Logs](../10-logs/) · [Master tracker](MASTER_TRACKER.md) · [00-START-HERE](../00-START-HERE.md)

---


## Deferring work — the carry convention

Work is often deferred to a later sub-step. Write it as:

```
carried to STEP-NNN.MM
```

**When that target closes, the line must say what became of the promise.** One of:

| Disposition | Means |
| --- | --- |
| `— discharged at STEP-NNN.MM` | the work was done, and where |
| `— withdrawn: <reason>` | the carry was mistaken |
| `— superseded by <what>` | it moved, and this says where |

`pnpm guard:carried-commitments` fails the build when a carry names an already
`VERIFIED` sub-step and the line says nothing.

**Why this is enforced rather than trusted.** `BUG-022`: `STEP-002.05` deferred
server-side session revocation with *"carried to STEP-002.07"*, `.07` closed <!-- carry-exempt: quotes BUG-022 -->
`VERIFIED` without it, and nothing failed for six sub-steps — because a carry is
prose and the documentation guard only checks that records exist. A security
control everybody believed existed did not.

**Re-routing is allowed and deliberately visible.** Writing `— superseded by` is
a legitimate answer; the point is that a promise which keeps moving can be
counted. Prose that *describes* a carry rather than making one is exempted with
`<!-- carry-exempt: reason -->`, the same shape as `rtl-exempt` in the CSS guard.

**What it cannot do:** prove the work was done. `— withdrawn: nonsense` passes.
It converts silence into a specific, recorded, reviewable claim — the same honest
limit as `contracts/baseline/BASELINE.md` §3.

## 1. Branching

| Branch | Purpose | Rules |
| --- | --- | --- |
| `main` | Always green, always deployable | **Direct pushes accepted while there is one owner (`ADR-017`)** — a pull request with no second reviewer is the author approving their own change with extra steps (`ADR-010`). `pnpm verify` before every commit and `pnpm ci:local` before anything touching dependencies or CI are what replace the merge gate. Every push triggers a graph refresh |
| `step/NNN-<slug>` | One branch per step | Sub-steps commit here sequentially |
| `fix/BUG-NNN-<slug>` | Bug fix | Must add a regression test before the fix |
| `chore/<slug>` | Tooling, dependencies | Still requires impact analysis if a version changes |

Short-lived branches are preferred. A step branch living longer than the step is a signal the step was sized wrong.

---

## 2. Commit conventions

```
STEP-NNN.MM: <imperative summary under 72 chars>

- Implements: REQ-…, REQ-…
- Blast radius: BR-NNN (LOW|MEDIUM|HIGH|CRITICAL)
- Regression: R1-R7 pass
- Tests: TST-…
- Closes: BUG-NNN (if applicable)
```

| Rule | Detail |
| --- | --- |
| **No AI attribution** | Commit messages and PR descriptions must not contain `Co-Authored-By: Claude`, "generated with", or any AI co-authorship trailer (`ADR-006`) |
| Traceable | Every commit references a sub-step and at least one requirement |
| Atomic | One logical change; mechanical renames separated from behavioral change |
| No WIP on `main` | Work-in-progress stays on the step branch |

---

## 3. Pull requests

| Requirement | Detail |
| --- | --- |
| Scope | One step branch, or one sub-step where review load demands it |
| Description | Requirements, sub-steps included, blast-radius links, regression results, screenshots for UI, migration plan |
| Required checks | Lint, types, unit, contract, integration, e2e, security scans, accessibility, data quality, AI evals, **change-impact record present** |
| Reviewers | Code owner **plus** one reviewer per affected consumer area (from the graph, not from memory) |
| Approval rule | The author may never approve their own change, and never be their own four-eyes approver |
| Merge | Squash or rebase preserving sub-step commit granularity where it aids history |

---

## 4. Definition of Ready (a step may start)

- [ ] Step file complete, all 28 sections
- [ ] **Named owner assigned** (currently blocked by `BLK-001`)
- [ ] All blocking dependencies resolved ([DEPENDENCY_REGISTER](DEPENDENCY_REGISTER.md))
- [ ] Open decisions blocking this step are closed
- [ ] Requirements have acceptance criteria and test IDs
- [ ] Sub-step files created from the template and reviewed
- [ ] Contracts identified (even if `PROPOSED`)
- [ ] Rollback approach known

## 5. Definition of Done (a step may be `VERIFIED`)

- [ ] Every sub-step complete per [SUB_STEP_PROTOCOL](SUB_STEP_PROTOCOL.md) §10
- [ ] Step acceptance criteria met with recorded evidence (step file §25, §26)
- [ ] All requirement test IDs passing
- [ ] Telemetry, alerts and runbook live with an owner
- [ ] Security, privacy and accessibility controls tested — not deferred
- [ ] Documentation current at the commit
- [ ] Post-change graph verification recorded
- [ ] Tracker updated by the owner

---

## 6. Escalation

| Situation | Action |
| --- | --- |
| Regression cross-check fails twice on the same sub-step | Stop; re-plan the sub-step with the step owner |
| Blast radius scores HIGH/CRITICAL | Owner approval before implementation |
| Graph `BLOCKED` on a security/privacy change | Escalate to Security Architect; static fallback alone is insufficient |
| Stop condition triggers ([RISK_REGISTER](RISK_REGISTER.md)) | Halt the phase; decision required from Product Lead |
| Assumption invalidated | Log in [DECISION_LOG](DECISION_LOG.md); re-plan affected steps |
| Cross-tenant exposure confirmed | **Immediate SEV1** incident; release halted |

---

## 7. Working agreement for coding agents

Agents operating in this repository follow the same rules as people, plus:

1. **Read `CLAUDE.md` first.** It carries the binding rules and the GitNexus workflow.
2. **Run impact analysis before editing any symbol**; report the blast radius before proceeding.
3. **Never rename with find-and-replace** — use `gitnexus_rename`.
4. **Run `detect_changes()` before committing.**
5. **Never claim a graph query, test run or verification that did not happen.** `BLOCKED` is acceptable; fabrication is not.
6. **Never disable or skip a failing test to go green** — log it as a bug.
7. **Never add AI attribution to commits.**
8. **One sub-step at a time**, with the regression cross-check between each.
9. **Update the logs** in [`10-logs/`](../10-logs/) as part of the same commit.
10. **Stop and ask** when a decision belongs to the owner rather than the implementer.

---

## 8. Cadence

| Ritual | Frequency | Output |
| --- | --- | --- |
| Sub-step close-out | Per sub-step | Logs, commit, push, re-index |
| Step close-out | Per step | Tracker `VERIFIED`, evidence recorded |
| Documentation freshness sweep | Weekly during delivery | Freshness table in [MASTER_TRACKER](MASTER_TRACKER.md) §8 |
| Risk and assumption review | Each phase gate | Re-scored register |
| Graph quality review | Each release | [GRAPH_QUALITY_AND_GOVERNANCE](../05-knowledge-graph/GRAPH_QUALITY_AND_GOVERNANCE.md) §1 |
| Incident retrospective | Per incident | Actions into the backlog and runbooks |
| DR and offline-sync drill | Quarterly | Rehearsal record |
