---
blast_radius_id: BR-034
sub_step_id: STEP-004.07
title: Client generation pipeline and no-hand-edit enforcement
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-034 — Client generation pipeline

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `73a2780` |
| HEAD at check | `73a2780` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** for the Python surface; the contract documents have no graph representation (`BR-029` §3, unchanged) |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(problem, upstream)` | Unchanged from `BR-029` — nothing in this sub-step touches it |
| 2 | `cypher(MATCH (n) WHERE n.filePath CONTAINS 'generated')` | **Ran after the exclusion landed.** One row: `tests/guards/generated-clients.sh`. No node from either generated client — the exclusion works (§4) |
| 3 | `detect_changes()` | Run pre-commit; recorded in the regression entry |

## 3. What this sub-step is

`contracts/openapi.yaml` has been authoritative since `.01`, but nothing was built
from it. It was a document that tests read. This sub-step makes it a **source**:

| Generated | From | By |
| --- | --- | --- |
| `packages/contracts/src/generated/openapi.ts` | `contracts/openapi.yaml` | `openapi-typescript` v6 |
| `apps/api/src/generated/models.py` | `contracts/openapi.yaml` | `datamodel-code-generator` |

Plus `tests/guards/generated-clients.sh`, which regenerates and diffs, and
`packages/contracts/src/contract.assert.ts`, which asserts at compile time that
the emitted types did not silently degrade.

## 4. Graph exclusion — the outcome is verified and my control is not what causes it

**Corrected after the post-commit re-index.** An earlier draft of this section
claimed `.gitnexusignore` excludes the generated directories. It does not, and the
distinction matters enough to state plainly.

### The requirement, which is met

The sub-step asks that generated paths not inflate graph coverage. Two reasons, and
the second is the one that matters:

- **It inflates coverage.** `REQ-KG-001`/`002` are gates on code a human maintains.
- **It makes impact analysis wrong in the direction that matters.** 71 generated
  Pydantic classes would each appear as a dependent of every shared schema, so a
  pre-change check on `Money` would report a blast radius in the hundreds. **A gate
  that always says HIGH is a gate that gets skipped.**

At `7b1489e`, with both clients committed, a Cypher query for nodes under either
generated path returns **nothing**. The requirement is met.

### What actually causes it

Not `.gitnexusignore`. Three measurements at the same commit:

| Configuration | files | nodes | edges |
| --- | --- | --- | --- |
| `.gitnexusignore` listing both generated directories | 353 | 5,702 | 7,993 |
| `.gitnexusignore` removed entirely | 353 | 5,702 | 7,993 |
| `.gitnexusignore` listing `tools/gen_clients.py` (probe) | — | **5,686** | — |

The third row is the control, and it is why the first two can be trusted. The
mechanism **works** — ignoring one hand-written module removed 16 nodes. Listing the
generated directories removes nothing, because **GitNexus already skips paths under
a `generated/` directory by default.**

### Why the file stays anyway

It is redundant today and it is kept deliberately, on the understanding that it is
documentation with a mechanism attached rather than the mechanism itself:

- A default is somebody else's decision and can change in a minor version.
- `packages/contracts/src/generated/` could be renamed to something the default does
  not recognise, and the requirement would silently stop being met.
- The reasoning above has to live somewhere a person will find it.

**What is NOT claimed:** that this repository has demonstrated control over graph
coverage of generated code. It has demonstrated that the coverage is currently
correct, and that the tool it would use to enforce that is functional. If GitNexus
changed its defaults tomorrow, nothing here would fail — there is no assertion on
the absence of generated nodes. That is a real gap, it is small, and it is carried
to `STEP-026` with the other graph limitations rather than papered over.

### An earlier measurement that was worthless

Before the commit, comparing indexes with and without the ignore file gave a 3-node
difference against 71 generated classes. The files were staged but uncommitted and
GitNexus did not parse them in that state. The number measured nothing, and the
first draft of this record said so rather than quoting it — which was right, but the
conclusion drawn alongside it (that the ignore file was doing the work) was still
wrong. **A correctly hedged measurement does not make the surrounding claim true.**

## 5. Change inventory

**Added**

| File | Purpose |
| --- | --- |
| `tools/gen_clients.py` | Both emitters over one contract |
| `packages/contracts/` | New workspace package — `package.json`, `tsconfig.json` |
| `packages/contracts/src/index.ts` | **Hand-written.** The package's public surface |
| `packages/contracts/src/contract.assert.ts` | **Hand-written.** 8 compile-time assertions |
| `packages/contracts/src/generated/openapi.ts` | Generated. 2,022 lines |
| `apps/api/src/generated/models.py` | Generated. 1,051 lines, 71 classes |
| `tests/guards/generated-clients.sh` | Regenerate-and-diff drift guard |
| `.gitnexusignore` | Graph exclusion |

**Modified**

| File | Change |
| --- | --- |
| `contracts/openapi.yaml` | **BUG-020** — `Evidenced.conflicts[]` recomposed from the shared schemas |
| `tests/api/test_api_operations.py` | The conflicts assertion rewritten from existence to substance |
| `tests/guards/meta/run-all.sh` | 4 meta-tests for the new guard |
| `package.json` | `contracts:generate`, `guard:generated-clients`, wired into `verify` |
| `README.md` | Regeneration workflow; 4 stale counts corrected |

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None. Both clients are additive and nothing imports them yet. `apps/api/src/generated/` is a new package under an existing tree, not a change to one |
| 2 | **Public API / contracts** | **One change, and it is a narrowing.** `Evidenced.conflicts[]` gained two required members and became closed (BUG-020). Every operation is `PROPOSED` and unimplemented, so there is no client to break — this is the last moment it is free |
| 3 | **Database / schema** | None |
| 4 | **Events** | None. `contracts/asyncapi.yaml` is **not** wired into the generator — see §9 |
| 5 | **Configuration** | `verify` gains a step. `.gitnexusignore` changes what the graph sees, not what runs |
| 6 | **Infrastructure** | Two dev dependencies: `openapi-typescript` **pinned to v6** (ADR-009, §8) and `datamodel-code-generator` |
| 7 | **Security** | Indirect but real. The generated error-code union is the register from `.01`; a client cannot branch on a code the server can never send. `contract.assert.ts` asserts that internal-only codes such as `ai.injection_detected` are **absent** from it |
| 8 | **Privacy** | Positive. `access_label` now survives into the conflict entry, so an `internal_only` conflicting value is identifiable as un-displayable rather than being shown or silently dropped |
| 9 | **Accessibility** | None |
| 10 | **Performance** | None at runtime. `verify` grows by ~20s |
| 11 | **Tenancy** | Unchanged and structurally preserved: no operation declares a tenant parameter, so no generated model has a tenant field to populate |
| 12 | **Documentation** | This record, `IMPL-031`, `BUG-020`, the regression entry, the sub-step record, parent §21, `MASTER_TRACKER`, README |

## 7. Mandatory data-flow inspection

Nothing executes yet, so what is inspected is **what the generated types permit** —
which is exactly what will be trusted once handlers exist.

| Hazard | Control | Evidence |
| --- | --- | --- |
| A schema degrading to `unknown` when an external `$ref` fails to resolve | `Exact<>` assertions, not `extends` — `extends` is satisfied by `unknown` on the right | Mutation-tested: retyping `Money.amount_minor` fails the build |
| Money arriving as a float | `Money` asserted exactly as `{amount_minor: number; currency: string}`, generated from the shared JSON Schema | Mutation-tested |
| An estimate typed loosely enough to be relabelled | `status` asserted as a closed pair; widening it to include a third member fails | Mutation-tested |
| A conflicting value shown when its licence forbids it | `access_label` required on the conflict's provenance and asserted to survive generation | BUG-020; mutation-tested |
| Staleness misread as disagreement | `validity` required on every conflict entry | BUG-020; mutation-tested |
| A client branching on a code the server cannot send | The error union is generated from `ERROR_MODEL.md` §3 via `.01`'s register, and asserted to be a union rather than `string` | Mutation-tested by degrading `ErrorCode` to `string` |
| An internal-only code reaching a client | `ai.injection_detected` asserted **absent** | Mutation-tested by inverting the check |
| A hand edit silently reverted by the next regeneration | The guard fails the build rather than letting the fix disappear | Mutation-tested, both directions (§8) |

## 8. What went wrong, and what it says

**`openapi-typescript` v7 does not run here — the third ADR-009 casualty.** v7 builds
its output through the TypeScript compiler API (`ts.factory.createKeywordTypeNode`).
TypeScript 7 is the native compiler and ships no JavaScript API. Pinned to v6, with
the reason recorded at the pin rather than in a changelog. BUG-017 was Next's
type-check step and BUG-018 was the token generator's module resolution; **three
tools have now assumed a JavaScript compiler API exists**, which makes it a property
of the ecosystem rather than a run of bad luck.

**The Python generator emitted a header that does not parse.** `--custom-file-header`
is inserted verbatim, so a plain header produced a module failing at import with
`SyntaxError: invalid character '—' (U+2014)`. Pre-commented before passing. Worth
naming plainly: *the generator does not check that its own output parses.*

**I copied `packages/ui`'s tsconfig into a package that is nothing like it.** It
declared `types: ["node"]` with no `@types/node` dependency, plus `jsx` and
`allowImportingTsExtensions` for tooling that does not exist here. `TS2688` on the
first typecheck. Replaced with a config derived from what the package actually
contains.

**`package.json` pointed `exports` at a file that did not exist.** Nothing imported
the package, so nothing failed. A broken entry point is invisible until the first
consumer, which is the worst time to find it.

**BUG-020 — see the register.** The generator found a contract defect that 470
Python assertions had read past, because they were reading the document that was
wrong. A second representation is a second reader.

## 9. What this sub-step deliberately does NOT do

**AsyncAPI is not wired into the generator.** `contracts/asyncapi.yaml` (`.05`)
declares 8 events, and no client is generated from it. `DEC-009` — queue versus
Kafka — is open, and the event client's shape depends on the answer: the envelope
is transport-independent but delivery semantics are not. Generating one now would
bake in an assumption this repository has explicitly refused to make. Carried to
`STEP-006`.

**No runtime validation is wired.** The Pydantic models exist; no handler uses them,
because no handler exists. `.08` covers compatibility, not adoption.

## 10. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every future handler and every future web caller consumes these types |
| Reversibility | High | Delete the generator and the packages; the contract is untouched by them |
| Detectability | High | 4 guard meta-tests, 8 mutation-verified compile-time assertions, 592 Python tests |
| Security exposure | Low–Medium | The error register reaches the client correctly and internal codes are asserted absent |
| Performance | None | No runtime path; `verify` +~20s |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 11. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **592 passed, 5 skipped** |
| Guard meta-suite | **47 passed, 0 failed** |
| Drift guard, both failure modes | Seeded and killed (§7) |
| Compile-time assertions | 8 seeded, 8 killed |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
