# Contract baseline — the thing compatibility is measured against

| Field | Value |
| --- | --- |
| Baseline version | `0.1.0` |
| Snapshot digest | `5706d69e0670e300` |
| Baseline commit | `eb30a26` |
| Established | 2026-08-11 (STEP-004.08) |
| Released to consumers | **No — see §2** |

> **The digest is checked.** `tests/guards/contract-compatibility.sh` hashes every
> file in this directory and fails the build if the result differs from the value
> above. Changing the snapshot therefore requires editing this table, which is
> where the version sits — so a baseline cannot move quietly.

`tests/guards/contract-compatibility.sh` diffs `contracts/` against this directory
and fails the build on a breaking change without a major version bump
(`REQ-PLAT-008`, [CONTRACT_CHANGE_POLICY](../../docs/product/04-contracts/CONTRACT_CHANGE_POLICY.md) §4).

---

## 1. Why a committed snapshot rather than a git tag

The policy says "diff against the previous release". Three ways to find that, and
only one of them survives contact with CI:

| Approach | Why not |
| --- | --- |
| `git show <tag>:contracts/openapi.yaml` | Requires tags to exist and the CI clone to be deep enough to reach them. A shallow clone — the default — silently has no tags, and a compatibility gate that silently passes is worse than none |
| Fetch the published spec over HTTP | The gate now depends on a network service being up, and on nobody having changed what it serves |
| **A committed snapshot** | The baseline is inspectable, reviewable in the pull request that changes it, and works in any clone with no network. **Chosen** |

The decisive argument is the second one: a change to the baseline is a diff a
reviewer sees. The other two hide the baseline somewhere no reviewer looks.

## 2. This baseline is pre-release, and that is recorded rather than implied

**No version of this API has been released to any consumer.** Every operation is
`PROPOSED`; no handler exists. So this snapshot is not "the last release" — it is
the point from which compatibility begins to be tracked.

That distinction matters for exactly one reason: **until the first release, a
breaking change is cheap and the right thing to do is take it.** BUG-020 in
STEP-004.07 narrowed `Evidenced.conflicts[]` and that was free because no client
existed. After release the same change costs a major version, a dual-run window and
a migration guide.

The gate still runs, and still fails on a breaking change without a version bump.
It runs now so that it is known to work before the day it matters, rather than
being switched on during the release that needs it.

## 3. Promoting the baseline

The baseline moves when a version is released, not when the contract changes. To
promote it:

```bash
pnpm contracts:baseline    # copies contracts/ over contracts/baseline/
```

then update the table at the top of this file — version, digest, commit, date — in
the **same commit**. `tests/guards/contract-compatibility.sh` enforces the pairing
by hashing the snapshot: if the contents differ from the recorded digest, the build
fails and names both values.

The digest is used rather than git history on purpose. `git diff` cannot see a
baseline that is not yet committed, answers differently before and after the commit
that introduces one, and needs history that a shallow CI clone does not have. A
content hash gives the same answer in every one of those situations.

**This is a speed bump, not a lock.** Anyone who can edit the contract can also
edit this file, and no guard in a repository can prevent its author from lying in
it. What the pairing does is convert "quietly rewrite the baseline so the diff comes
out empty" into "claim a release that did not happen" — a specific, recorded,
reviewable false statement. That is the honest limit of what this check achieves.

## 4. What the diff cannot see

**Semantic change.** A field that keeps its name, type and required-ness while
changing what it means passes every check here. `CONTRACT_CHANGE_POLICY` §1 calls
that the most dangerous category, and it is invisible to a structural diff by
construction — see `tools/contract_diff.py` and `ENH-001`, which proposes a partial
mitigation and has not been accepted.

A green compatibility check is evidence that a change is not breaking in a way a
machine can recognise. It is not evidence that the change is safe.
