# ADR-013 — Auth0 is the identity provider (DEC-004 resolved)

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-06 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Context:** `DEC-004` had been open since `STEP-002` was written and was deferred three times — `.01`, `.02` and `.04` were all built behind a verifier *port* so the decision stayed reversible. `STEP-002.05` is where deferral stops working: `REQ-SEC-003` requires "OIDC with passkey support" and the acceptance criteria are that sign-in, refresh and sign-out actually work. A port cannot be exercised against nothing.
- **Decision:** **Auth0** is the managed OIDC provider.
- **Consequences:**
  - **Cloud-neutral, so `DEC-007` stays open.** Choosing AWS Cognito would have decided the cloud provider as a side effect of an identity decision; that was the main reason it was rejected.
  - Mature WebAuthn/passkey support, which `REQ-SEC-003` requires.
  - Standards-compliant OIDC, so `apps/web/src/auth/oidc.ts` is a thin adapter over discovery, authorization-code-with-PKCE and refresh rotation. The session layer above it knows nothing about Auth0.
  - Auth0 **Organizations** maps to the advisor/org workspace in `STEP-028`, so Phase 4 does not need a second identity system.
  - **Refresh-token rotation makes single-flight refresh mandatory, not an optimisation.** Rotation invalidates the previous refresh token the moment one is redeemed, so two concurrent refreshes present a just-revoked token; Auth0 treats that as replay and can revoke the whole token family, signing the user out. `refresh.ts` coalesces per session for exactly this reason.
  - **Cost, stated plainly:** the free tier covers Phase 1, and Auth0's pricing rises steeply with monthly active users. This is a commercial dependency with a real exit cost once user data lives in it. The review trigger below is not a formality.
  - **Not yet verified against a live tenant.** The flows are exercised against a spec-compliant provider in tests; no Auth0 account exists. Passkey enrolment, tenant rate limits and rotation behaviour under genuine concurrency are **unproven**. See `BR-014` §9.
- **Alternatives rejected:**
  - **Clerk** — best Next.js developer experience, but its value is prebuilt UI, and `STEP-003` builds our own WCAG 2.2 AA design system. Using its components would put the sign-in surface outside our accessibility control, which `REQ-A11Y-001` does not allow.
  - **AWS Cognito** — cheapest at scale, but selecting it would pre-empt `DEC-007`, and its passkey support is the least mature of the candidates.
  - **WorkOS** — strongest for enterprise SSO/SCIM and attractive for `STEP-028`, but heavier than Phase 1 needs and less focused on consumer guest/passkey flows.
  - **Self-hosted Keycloak** — no vendor lock-in, but commits a single-owner project to operating an identity service, which `ADR-010`'s staffing reality does not support.
- **Review trigger:** Monthly active users approach the paid tier boundary; `DEC-007` resolves in a way that makes a cloud-native provider materially cheaper; or passkey support proves inadequate in practice.

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [ADR-014](ADR-014-guest-session-lifetime.md) — the guest-session counterpart decided alongside this
- [BR-014](../product/10-logs/blast-radius/BR-014-browser-session.md) — the change that forced it
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
