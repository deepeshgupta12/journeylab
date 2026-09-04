---
blast_radius_id: BR-060
sub_step_id: STEP-007.02
title: Public coverage page, and the API application it needed
author: Deepesh Kumar Gupta
date: 2026-09-04
score: MEDIUM
confidence: MEDIUM
approval_required: true
---

# BR-060 — The coverage page

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `5d3cd5b` |
| HEAD at check | `5d3cd5b` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — `RISK-016` |

## 2. Queries run

| Symbol | Graph | Grep |
| --- | --- | --- |
| `DataTable` | 0, LOW | 9 |
| `toCsv` | 1, LOW | 11 |
| `getCoverage` | 0, **UNKNOWN** | 3 |

`getCoverage` returns `UNKNOWN` because the graph indexes the Python and TypeScript
definitions separately and neither is a caller of the other — the call it cannot see
is the HTTP one, which is the whole subject of this sub-step. A reminder that the
graph describes imports, not systems.

## 3. The page needed a server, and that was a real decision

`.01` built the handler; `BR-059` §9 recorded that nothing routed to it. Two ways to
get data onto a page:

| | Consequence |
| --- | --- |
| Query Postgres from Next.js | `ADR-003` declares **one** deployable API application, and `module-boundaries.sh` already forbids `apps/web` importing `services/`. It would also duplicate the aggregate-health rule `REQ-EVID-006` depends on, in a second language — which is exactly how `BUG-029` happened between a projection and a contract |
| Serve it over HTTP | The architecture as declared |

So `apps/api/src/app.py` is a **precondition** of this page rather than scope creep,
the same way `BUG-027`'s fix was a precondition of entity resolution. It is one route,
one dependency, and no middleware this sub-step does not need.

**The error code did not exist, and `problem()` refused to invent one.** A database
failure serving a public endpoint had no registered code, and the builder rejects
unknown ones by design. The honest fix was to add the row to `ERROR_MODEL.md`,
regenerate `error_codes.py` and `error-codes.json`, regenerate the TypeScript client,
and run the compatibility gate — which classified it additive. Reaching for
`coverage.provider_degraded` would have been faster and would have told a client the
wrong thing about what failed.

## 4. Owner approval: the reserved port block was full

5700–5707 are infrastructure, 5708 is the Playwright harness, 5709 is the developer's
HTTPS dev server. There was no free port, and `port-collisions.sh` exists because of
a real incident — *"5544 looked free to `lsof` only because Saakshya was stopped"*.

Picking 5710 because it looked free would have been precisely that mistake, so the
owner was asked and **approved extending the block to 5710**. The guard's range, the
README and the Playwright harness were updated together.

This is the `approval_required: true` on this record, and unlike `BR-050`'s it is a
real second party: the constraint is about the owner's machine, which I cannot inspect.

## 5. Two guards were wrong, and one of them was wrong before today

**`readme-accuracy.sh` scanned every `| 570X |` row** anywhere in the file and
asserted each was published by compose. That held while the only such table listed
containers. This sub-step added a second table for **application** ports — Playwright,
the dev server, the API — none of which compose publishes, so all three were reported
missing.

The guard's subject was inferred from a number rather than stated. It now reads
between `<!-- compose-ports -->` markers, so a third table cannot break it by looking
similar, and the range widened from `570[0-9]` to `5[0-9]{3}` — a documented port
outside the old block would previously have escaped the check entirely.

Checked with a seeded row (`| 5799 | Invented service |`), which it rejects.

## 6. What the browser suite now proves

40 → **56 tests**, and the page is in the axe surface list from its first commit
rather than added later.

The behavioural assertions are the acceptance criteria, not a rendering smoke test:
no cookie is set at all (`REQ-PRIV-001` — a session issued to a visitor reading a
public page is an identifier nobody asked for); no supplier name appears anywhere in
the DOM; **there is no map to disable**, which is a stronger statement than
`REQ-A11Y-003`'s and only available because the table was built first; and the empty
state says *"no region has been declared yet"* rather than rendering an empty table,
because "nothing is declared" and "we could not ask" are different facts and only one
is about coverage.

**The accessibility run now depends on the API being up.** If it fails to start these
tests fail, which is correct — a coverage page rendered against no data would pass axe
and prove nothing about the surface being shipped.

## 7. Assessment

| Category | Assessment |
| --- | --- |
| Code | `apps/api/src/app.py`, `apps/web/src/app/coverage/*` — new |
| Contract | **`platform.dependency_unavailable` added** at its source and regenerated. Compatibility gate: additive |
| Schema | None |
| Security | The page reads no session and sets no cookie. The DSN cannot reach a client — asserted with a password in it |
| Accessibility | axe clean in both device profiles; the page is in the surface list |
| Infrastructure | Port block extended to 5710, owner-approved |

**Mutation testing: 7 seeded, 7 killed**, including a health check that queries the
database and a driver error interpolated into the response.

## 8. What this does not close

| Gap | Why |
| --- | --- |
| No region is declared, so the page renders empty | Deliberate. Declaring one is a product decision `017` forces to be made rather than defaulted |
| The API has no middleware, rate limiting or CORS | Not needed by one public read; each belongs where its first caller does |
| `pnpm api` is a foreground process | Process supervision is operations work |
| The CSV assertion checks the control exists | The export itself is covered in the design-system suite; duplicating it here would test `DataTable` twice and the page not at all |

## 9. Score

**MEDIUM.** A new process, a contract addition and an infrastructure change — but the
route is one public read against an empty table, and every guarantee it makes is
tested. Owner approval obtained for the block extension.
