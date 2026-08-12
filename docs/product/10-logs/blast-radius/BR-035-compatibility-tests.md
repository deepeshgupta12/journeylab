---
blast_radius_id: BR-035
sub_step_id: STEP-004.08
title: Backward-compatibility and consumer contract tests
author: Deepesh Kumar Gupta
date: 2026-08-12
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-035 — Backward-compatibility and consumer contract tests

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `eb30a26` |
| HEAD at check | `eb30a26` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(generate_typescript, upstream, includeTests)` | 1 direct (`main`), 1 process, LOW, `epistemic: exact`. The generator is self-contained, so `.08` adding a second tool alongside it cannot disturb it |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

The sub-step record predicted `BR-029`, which STEP-004.02 holds. Corrected to
`BR-035` in the sub-step file.

## 3. What this sub-step is

`REQ-PLAT-008`: a breaking contract change fails CI unless it carries a new major
version. Four pieces:

| Piece | File |
| --- | --- |
| The classifier | `tools/contract_diff.py` |
| The gate | `tools/check_compatibility.py`, `tests/guards/contract-compatibility.sh` |
| The baseline | `contracts/baseline/` + `BASELINE.md` |
| Consumer expectations | `tests/contracts/test_consumer_contracts.py` |

### The one idea worth reading the code for

**Request and response schemas have opposite compatibility rules**, and a differ
that treats a schema as a schema is wrong about half of them.

| Edit | In a request | In a response |
| --- | --- | --- |
| Add a required property | **BREAKING** | additive |
| Remove a property | potentially breaking | **BREAKING** |
| Make required → optional | additive | **BREAKING** |
| Make optional → required | **BREAKING** | additive |
| Remove an enum value | **BREAKING** | potentially breaking |
| Add an enum value | additive | **potentially breaking** |

Every row inverts. So the classifier walks the document **from its operations**,
records which position each schema is reachable in, and applies the matching rules.
A schema reachable from both — `Money` and `Problem` are — is checked under both
and takes the worse verdict.

Half the test suite is written as pairs asserting opposite severities for the same
edit. A direction-blind classifier fails one of each pair; a classifier that shouts
"breaking" at everything fails every additive case. Neither can pass the pairs.

## 4. Why the baseline is a committed snapshot

The policy says "diff against the previous release", and there is no release.

| Candidate | Rejected because |
| --- | --- |
| `git show <tag>:contracts/openapi.yaml` | Needs tags and a deep clone. A shallow CI clone silently has neither, and a compatibility gate that silently passes is worse than none |
| Fetch the published spec | Makes the gate depend on a network service being up and unchanged |
| **Committed snapshot** | Inspectable, reviewable in the pull request that moves it, works offline. **Chosen** |

The decisive argument is reviewability: a change to the baseline is a diff somebody
sees.

**The bypass, and its honest limit.** Anyone can defeat a compatibility gate by
moving the baseline. That is prevented as far as it can be: `BASELINE.md` records a
digest of the snapshot, the gate recomputes it, and a mismatch fails the build. This
does not make the bypass impossible — the author can edit both — it converts a
silent edit into **a claimed release that did not happen**, which is a specific,
recorded, reviewable false statement. `BASELINE.md` §3 says so in those words rather
than implying the check is stronger than it is.

The digest is used **instead of git history** because `git diff HEAD` cannot see an
uncommitted baseline, answers differently either side of the commit that introduces
one, and needs history a shallow clone lacks.

## 5. Change inventory

**Added**

| File | Purpose |
| --- | --- |
| `tools/contract_diff.py` | Direction-aware classifier |
| `tools/check_compatibility.py` | The gate's decision |
| `tools/promote_baseline.py` | `pnpm contracts:baseline` |
| `tests/guards/contract-compatibility.sh` | Gate entry point |
| `contracts/baseline/` | Snapshot + `BASELINE.md` |
| `tests/contracts/test_contract_compatibility.py` | 57 assertions |
| `tests/contracts/test_consumer_contracts.py` | Consumer expectations |

**Modified**

| File | Change |
| --- | --- |
| `contracts/openapi.yaml` | **BUG-021** — `JobEvent.sequence` required |
| `contracts/asyncapi.yaml` | **BUG-021** — `model_versions` required |
| `tests/api/test_api_operations.py` | Two assertions strengthened |
| `tests/api/test_event_contracts.py` | One assertion strengthened |
| `tests/guards/meta/run-all.sh` | 8 meta-tests |
| Both generated clients | Regenerated for the BUG-021 change |
| `package.json`, `README.md` | Scripts and documentation |

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None. Two new tools, called only by the gate |
| 2 | **Public API / contracts** | Two fields became required in **response/event** shapes. Additive by the classifier's own rules and confirmed by it in the gate's output |
| 3 | **Database / schema** | None |
| 4 | **Events** | `ScenarioSetGenerated` requires `model_versions`. AsyncAPI is **not** diffed by the gate — see §9 |
| 5 | **Configuration** | `verify` gains a step |
| 6 | **Infrastructure** | None. No new dependency |
| 7 | **Security** | Indirect. The gate makes silent removal of an error code or an auth-bearing parameter a build failure |
| 8 | **Privacy** | Positive. `accessibility_needs` is now pinned to an array of strings and asserted **not** required — a required sensitive attribute is a compelled disclosure (`REQ-PRIV-003`) |
| 9 | **Accessibility** | None |
| 10 | **Performance** | None at runtime; `verify` +~2s |
| 11 | **Tenancy** | Unchanged. Still no tenant parameter on any operation |
| 12 | **Documentation** | This record, `IMPL-032`, `BUG-021`, `ENH-001`, the regression entry, sub-step record, parent §21, `MASTER_TRACKER`, README |

## 7. Mandatory data-flow inspection

Nothing executes. What is inspected is what the gate **permits to change**, since
that is what everything downstream will trust.

| Hazard | Control | Evidence |
| --- | --- | --- |
| A removed operation reaching a release | `operation_removed` ⇒ BREAKING | Seeded and killed |
| A response field quietly dropped | `response_property_removed` ⇒ BREAKING | Seeded and killed |
| A guarantee relaxed without notice | `response_property_became_optional` ⇒ BREAKING | Unit-tested |
| A client method renamed invisibly | `operation_id_changed` ⇒ BREAKING even though the wire is unchanged | Unit-tested |
| A deprecation with no end date | Both `Deprecation` and `Sunset` required | Seeded and killed |
| **The gate bypassed by moving the baseline** | Snapshot digest recorded in `BASELINE.md` and recomputed | Seeded and killed |
| A version claimed that the snapshot does not declare | Marker version compared to `info.version` | Seeded and killed |
| A legitimate breaking change blocked forever | A major bump permits it, and the gate says which §3 obligations it does **not** check | Seeded and confirmed to PASS |
| An error code silently removed | The code enum is a response field; removal is reported | Covered by the enum rules |

## 8. What the audit found — the promised hunt

The `.07` record committed `.08` to hunting the existence-versus-capability
assertion pattern deliberately, having hit it four times in six sub-steps.

Grepping every `assert "x" in ...properties` in the contract suites produced three
candidates. **Two were real defects** (`BUG-021`): `JobEvent.sequence` and
`ScenarioSetGenerated.model_versions` were both optional while their descriptions
promised gap detection and reproducibility. The third, `accessibility_needs`, was
correct but under-asserted and was pinned to its real shape in the same pass.

**The pattern found defects when hunted and had not surfaced them in four sub-steps
of ordinary work.** That is the argument for scheduling this kind of audit rather
than relying on noticing.

**It also caught one of my own, twice.** My first version of the orphan-schema test
asserted `len(orphans) <= 2` and failed on three; raising the threshold would have
made it pass and assert nothing. The property worth holding is that an unreferenced
schema must be a bare `$ref` alias — a named export — rather than an inline
definition nobody references. And my consumer expectations named a schema
`TripCreate` that does not exist; the contract calls it `CreateTripRequest`. Written
from assumption rather than from the document, which is the failure named in the
STEP-003 e2e work.

## 9. What this sub-step deliberately does NOT do

**AsyncAPI is not diffed.** Only `openapi.yaml` is compared against the baseline.
The snapshot includes `asyncapi.yaml` so the baseline is complete, but no event
compatibility rules are implemented. Event compatibility turns on delivery
semantics — redelivery, ordering, partitioning — and `DEC-009` (queue versus Kafka)
is open. Written now, the rules would encode an assumption this repository has
explicitly refused to make. **Stated here rather than left to be discovered from an
empty diff.** Carried to `STEP-006`.

**Semantic change is not detected**, per `CONTRACT_CHANGE_POLICY` §1 and the
sub-step's own note. `ENH-001` proposes a partial mitigation and is **PENDING an
owner decision** — logged rather than implemented, per the enhancement log's rule 1.

**`POTENTIALLY_BREAKING` does not fail the build.** §2 says such changes are
breaking "unless consumer analysis proves otherwise via the code graph", and that
analysis is a human's. Failing on it would fire on every added enum value, and a
gate routinely overridden has stopped being a gate. It is printed prominently and
named as requiring the §2 analysis.

## 10. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every future contract change passes through this gate |
| Reversibility | High | Two tools, one guard, one snapshot directory |
| Detectability | High | 57 classifier assertions, 8 guard meta-tests, all seeded |
| Security exposure | Low | No runtime path; the gate makes silent removals loud |
| Performance | None | ~2s added to `verify` |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 11. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | Recorded in the regression entry |
| Guard meta-suite | 8 new cases, all seeded and killed |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
