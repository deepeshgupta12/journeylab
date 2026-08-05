# ADR-009 — TypeScript 7.0.2 supersedes the documented 6.0 baseline

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Context:** The blueprint baseline (§10, August 2026) specifies TypeScript 7.0, and `ASM-004` requires version revalidation before pinning. At implementation time `npm view typescript dist-tags` reports **`latest: 7.0.2`**; 6.0.3 is a real stable release but no longer current. Portfolio standard §4.18 requires *current stable/LTS at implementation time*, which is what triggered the revalidation rather than a preference for novelty.
- **Decision:** Pin **TypeScript 7.0.2**. This supersedes the 6.0 baseline for this repository.
- **Verified evidence:** `tsconfig.base.json` compiles clean under 7.0.2 (exit 0) with an ESM package, and `noUncheckedIndexedAccess` still rejects an unguarded index access (exit 1). Both checked by explicit exit code, not by output inspection.
- **Consequences:** Blueprint §10 and every doc citing "TypeScript 7" is now stale and updated. **Every package must declare `"type": "module"`** — under `module: nodenext` with `verbatimModuleSyntax`, TS 7 treats a package without it as CommonJS and rejects top-level `export`. This surfaced during validation and is a real constraint on `STEP-002` onward, not a theoretical one. Dependency surface at decision time was minimal: 0 TypeScript source files.
- **Alternatives rejected:** Staying on 6.0.3 (contradicts §4.18's current-stable requirement once 7 is `latest`); waiting until source exists (a major-version migration is cheapest at zero files).
- **Review trigger:** TypeScript 8, or a breaking incompatibility with Next.js 16.2 / React 19.2.

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
