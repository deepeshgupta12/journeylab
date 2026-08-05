# JourneyLab — Regression Cross-Check Log

| Field | Value |
| --- | --- |
| Owner | Implementing engineer per entry |
| Status | `READY` — no entries; no implementation has occurred |
| Rule | **One entry per sub-step.** A sub-step without a passing entry may not be committed |
| Origin | Repository-owner directive: previous implementations and fixes must not break |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Sub-step protocol](../02-delivery/SUB_STEP_PROTOCOL.md) · [Change impact protocol](../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md) · [Bug register](BUG_REGISTER.md)

---

## The seven checks

Run **after** the sub-step's own tests pass and **before** committing.

| # | Check | What it protects | Pass condition |
| --- | --- | --- | --- |
| **R1** | Full regression suite — this step's completed sub-steps **and** every `VERIFIED` step | Accumulated work | All green; no unexplained skips |
| **R2** | Contract compatibility vs. last release | Consumers | No unintended breaking diff |
| **R3** | `detect_changes()` graph diff | Unintended blast radius | Only expected symbols and flows changed |
| **R4** | Untested-requirement count (`KG-Q-008`) | Coverage erosion | Not increased |
| **R5** | Orphan / unowned node count (`KG-Q-008`) | Governance erosion | Not increased |
| **R6** | Every closed bug's regression test | Fixed bugs staying fixed | All passing |
| **R7** | Cross-tenant isolation (`TST-SEC-002`) | The one thing that must never break | Pass — **non-negotiable** |

**R4 and R5 are ratchets.** They may improve or stay flat; they may never worsen. This is what stops quality debt accumulating one "just this once" at a time.

---

## Entry format

```markdown
## STEP-NNN.MM — YYYY-MM-DD — <sub-step title>

| Field | Value |
| --- | --- |
| Commit | `<sha>` |
| Author | |
| Graph indexed commit | `<sha>` — matched HEAD? |
| Duration | |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | PASS / FAIL | N tests, M skipped (reasons) |
| R2 contract compatibility | PASS / FAIL | diff summary |
| R3 graph diff expected | PASS / FAIL | new/removed nodes and edges |
| R4 untested requirements | PASS / FAIL | before → after |
| R5 orphan/unowned nodes | PASS / FAIL | before → after |
| R6 closed-bug tests | PASS / FAIL | N tests |
| R7 tenant isolation | PASS / FAIL | |

**Overall:** PASS / FAIL

### Failures and resolution
| Check | Failure | Cause | Resolution | Bug ID |
| --- | --- | --- | --- | --- |

### Notes
Anything a future reader should know — flaky tests identified, durations
trending up, coverage gaps accepted with a reason.
```

---

## Entries

*No entries. Implementation has not begun.*

The first entry will be for `STEP-001.01`.

---

## Handling failures

| Situation | Action |
| --- | --- |
| A check fails | **Sub-step is not done.** Fix forward or revert |
| Failure reveals a defect | Log `BUG-NNN`, add a regression test, then re-run |
| Same sub-step fails twice | Stop; re-plan with the step owner ([WAYS_OF_WORKING](../02-delivery/WAYS_OF_WORKING.md) §6) |
| A test is flaky | Log as a bug; **quarantining requires an owner and a deadline**, never silent deletion |
| R7 fails | **Immediate SEV1.** Halt all work; incident response |
| R4/R5 would worsen | Either add the missing test/owner now, or record an explicit, approved exception with an expiry date |

**Never disable a failing test to make a check pass.** That converts a visible problem into an invisible one and is itself logged as a bug.

---

## Suite growth expectations

The R1 suite grows with every sub-step, which is the point — and also a cost. Manage it deliberately:

| Concern | Approach |
| --- | --- |
| Runtime growth | Parallelise; tier into fast (every sub-step) and full (pre-push, pre-release) as defined in `STEP-027` |
| Slow suite tempting shortcuts | Track suite duration in this log; a trend upward is a scheduled task, not a reason to skip |
| Redundant tests | Prune only with owner approval and a recorded rationale |
| Fast tier must always include | R7 tenant isolation, R6 closed-bug tests, contract compatibility |
</content>
