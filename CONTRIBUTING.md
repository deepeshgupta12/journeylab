# Contributing to JourneyLab

**Owner:** Deepesh Kumar Gupta (`@deepeshgupta12`) — [ADR-010](docs/product/02-delivery/DECISION_LOG.md)

Read [`CLAUDE.md`](CLAUDE.md) first — it is the condensed working agreement for
humans and agents alike. Full documentation: [`docs/product/`](docs/product/00-START-HERE.md).

---

## Non-negotiable rules

1. **No change without a pre-change impact record** — code, schema, API, event,
   model, prompt, infrastructure or config (`REQ-KG-008`,
   [protocol](docs/product/05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md)).
2. **Work one sub-step at a time**, each ending in a regression cross-check,
   documentation update, commit and push
   ([protocol](docs/product/02-delivery/SUB_STEP_PROTOCOL.md)).
3. **Run the regression cross-check (R1–R7) before every commit.**
4. **No AI co-authorship attribution** in commit messages or PR descriptions
   ([ADR-006](docs/product/02-delivery/DECISION_LOG.md)) — no `Co-Authored-By: Claude`,
   no "generated with" line.
5. **Never claim a query, test or verification that did not happen.** `BLOCKED` is
   an acceptable answer; a fabricated one is not.
6. **Never disable or skip a failing test to go green** — log it as a bug.
7. **Never rename with find-and-replace** — use `gitnexus_rename`.

## Before you start

```bash
nvm use || export PATH="/opt/homebrew/opt/node@24/bin:$PATH"   # Node 24 LTS
pnpm install
uv sync
pnpm verify          # must be green before you change anything
npx gitnexus status  # must be current at HEAD
```

## The loop

```
pick sub-step → pre-change analysis → blast radius (BR-NNN) → implement
  → tests pass → regression R1–R7 → detect_changes() → update docs + logs
  → commit → push → npx gitnexus analyze
```

### Regression cross-check (R1–R7)

| # | Check | Pass condition |
| --- | --- | --- |
| R1 | Full regression suite | All green; no unexplained skips |
| R2 | Contract compatibility | No unintended breaking diff |
| R3 | `detect_changes()` graph diff | Only expected scope changed |
| R4 | Untested requirements | **Not increased** (ratchet) |
| R5 | Orphan / unowned nodes | **Not increased** (ratchet) |
| R6 | Closed-bug regression tests | All passing |
| R7 | Tenant isolation | **Pass — non-negotiable** |

A failure means the sub-step is not done. Fix forward or revert; never proceed red.

## Commit format

```
STEP-NNN.MM: <imperative summary under 72 chars>

- Implements: REQ-…
- Blast radius: BR-NNN (LOW|MEDIUM|HIGH|CRITICAL)
- Regression: R1-R7 pass
- Tests: TST-…
- Closes: BUG-NNN (if applicable)
```

Branches: `step/NNN-<slug>`, `fix/BUG-NNN-<slug>`, `chore/<slug>`.
`main` is protected — no direct pushes once branch protection is enabled.

## Guards

`pnpm verify` runs the fast tier. Every guard is **meta-tested**: proven to fail
against a seeded violation, asserting the specific rule and exit code. A guard that
has never been shown to fail is not a guard.

| Guard | Protects against |
| --- | --- |
| `no-stray-markup.sh` | BUG-001 — authoring markup leaking into files |
| `no-tracked-artifacts.sh` | BUG-002 — dependencies/build output committed |
| `module-boundaries.sh` | ADR-003 — cross-package reach-ins |
| `typecheck.sh` / `py-typecheck.sh` | Type regressions |

## Documentation is part of the change

Update in the **same commit**: the sub-step record, the relevant log in
[`docs/product/10-logs/`](docs/product/10-logs/), the blast-radius record, the step
file §21, and [MASTER_TRACKER](docs/product/02-delivery/MASTER_TRACKER.md).

**MASTER_TRACKER is the only source of delivery status.** Never maintain competing
status elsewhere.

## Known gap

**Four-eyes approval is structurally unsatisfiable** with one owner
([ADR-010](docs/product/02-delivery/DECISION_LOG.md)). The author is currently also
the approver, which conflicts with
[WAYS_OF_WORKING](docs/product/02-delivery/WAYS_OF_WORKING.md) §3. The automated
gates therefore carry proportionally more weight — do not weaken them.
