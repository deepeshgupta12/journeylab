# ADR-017 — Direct pushes to `main`, for as long as there is one owner

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited**.

- **Date:** 2026-08-13 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Decision type:** **Owner directive** — "commit and push the way you push".

## Context

`WAYS_OF_WORKING` §4 has said since STEP-001: *"`main` — Protected; no direct
pushes"*. Every commit in this repository has gone straight to `main`.

I justified that for most of this session on a false premise: I stated repeatedly
that `gh` was not authenticated and that pull requests were therefore unavailable.
**That was wrong.** `gh auth status` reports a logged-in account, and I only
discovered it when checking a CI run. The practice was right for a different
reason than the one I gave, and the documentation said the opposite of both.

`ADR-010` already records the underlying condition: **one owner means four-eyes
review is structurally unsatisfiable.** A pull request in a single-owner
repository is the author approving their own change with extra steps.

## Decision

**Direct pushes to `main` are the accepted workflow while `ADR-010` holds.**
`WAYS_OF_WORKING` §4 is corrected to say so rather than describing a rule nobody
follows.

## Consequences

- **The documentation matches the practice.** A rule that is universally violated
  trains readers to treat the whole document as aspirational, which is more
  expensive than the rule was worth.
- **The automated gates carry the review load, and that was already true.**
  `ADR-010` said it; this makes it explicit. `pnpm verify` is 25 steps across 19
  guards, R7 runs on every push (`STEP-001.07`), and every closed bug keeps a
  regression test. Review is a self-check, so the gates are the control.
- **`main` must stay green by construction**, since nothing stands between a
  commit and the default branch. `pnpm verify` before every commit and
  `pnpm ci:local` before anything touching dependencies or CI are not optional
  under this decision — they are what replaces the merge gate.
- **This is a governance debt, not a governance decision.** It is recorded as
  accepted because a solo repository has no better option, not because it is
  good. `REQ-ADMIN-002` four-eyes overrides and `SC-GOV-02` remain
  **unsatisfiable**, exactly as `ADR-010` states, and `STEP-021` still cannot ship
  without an answer.

## What would reverse this

A second contributor. At that point the reason for the exception disappears in the
same moment the ability to satisfy the rule appears, and this ADR is superseded
rather than amended.

## Alternatives rejected

- **Open pull requests and self-merge.** Produces a review artefact with no
  reviewer. `WAYS_OF_WORKING` §3 already says the author may never approve their
  own change; a self-merged PR is that, formalised, plus latency.
- **Leave the documentation as-is and keep pushing directly.** The status quo, and
  the reason this ADR exists: a repository whose written rules are contradicted by
  every commit in its history has a credibility problem that no individual rule is
  worth.

## Review trigger

A second contributor joins, or `STEP-021` reaches implementation — the same
triggers as `ADR-010`, because it is the same underlying condition.

---

## Related
- [ADR-010](ADR-010-repository-ownership.md) — the single-owner condition this follows from
- [WAYS_OF_WORKING](../product/02-delivery/WAYS_OF_WORKING.md) §4 — corrected by this
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md)
