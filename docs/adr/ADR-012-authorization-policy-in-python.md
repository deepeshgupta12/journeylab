# ADR-012 — The authorization policy is Python, co-located with enforcement

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-06 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Context:** `STEP-002.03` §2 names `packages/authz/src/policy.ts` — a TypeScript package. But `REQ-SEC-004` requires every operation to enforce role and resource-relationship checks **server-side**, and since `STEP-002.02` the server is Python/FastAPI (`TECHNICAL_ARCHITECTURE`: "Application services — Python 3.14 + FastAPI", Confirmed). A TypeScript module cannot make the decision inside a Python request without an RPC hop, which would put a network boundary — and a failure mode — inside the authorization path. The same sub-step's §8 states that client-side role checks are "presentation only", which confirms the TypeScript surface was never intended to be the authority.
- **Decision:** The authoritative policy lives in **`apps/api/src/authz/`** in Python, beside the boundary that enforces it. The path named in the sub-step file is superseded and the sub-step record has been corrected.
- **Consequences:**
  - The decision point is an in-process function call. No network hop, no serialization, no partial-failure mode inside authorization.
  - It reuses `RequestContext` and `opaque_denial` from `STEP-002.02` directly, so denial shape cannot drift between authentication and authorization.
  - `AUTHORIZATION_MATRIX.md` becomes the single source: `apps/api/src/authz/matrix.py` is **generated** from it, and a drift test fails CI if the two disagree.
  - **Cost, stated plainly:** if the frontend later wants to grey out forbidden actions, it needs the same matrix in TypeScript. That must be **generated from the same markdown**, never hand-maintained — two hand-written copies of an authorization matrix will diverge, and the divergence will be silent. The generator already isolates parsing in `tools/authz_matrix_source.py` so a second emitter is additive.
  - A documented file path was contradicted. Recorded here rather than quietly implemented elsewhere.
- **Alternatives rejected:**
  - **TypeScript as specified** — cannot enforce server-side in a Python request; would make `REQ-SEC-004` unsatisfiable as written.
  - **TypeScript policy behind an RPC** — puts a network dependency in the authorization path; an outage becomes either a denial storm or, worse, a tempting fail-open.
  - **Both languages, hand-maintained** — guarantees eventual divergence in the one table where divergence is a vulnerability.
- **Review trigger:** The frontend needs presentation-level permission hints (STEP-003), or a second backend language appears.

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [ADR-011](ADR-011-psycopg3-as-the-postgres-driver.md) — the other implementation decision this boundary forced
- [BR-012](../product/10-logs/blast-radius/BR-012-authorization-policy.md) — the change that raised it
- [AUTHORIZATION_MATRIX](../product/04-contracts/AUTHORIZATION_MATRIX.md) — the generating source
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
