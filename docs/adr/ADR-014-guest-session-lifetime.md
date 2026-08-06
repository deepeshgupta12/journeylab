# ADR-014 — A guest session lasts 7 days

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-06 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Context:** `REQ-PRIV-001` guarantees a guest can plan a trip without providing an email. That guarantee has a consequence the `STEP-002.05` record states directly: "a guest token is a bearer capability — anyone holding the link holds the trip." With no email there is **no recovery channel and no revocation channel**. Expiry is therefore the only control bounding both loss and leak, and its duration is a product decision that was never made. `STEP-008` also flags guest-session lifetime as an open question (`ASM-014`).
- **Decision:** A guest session lasts **7 days** from issue, enforced server-side, with a warning surfaced in the final **24 hours**.
- **Consequences:**
  - Covers the 3–7 day trip length that is Phase 1 MVP scope, across several planning sittings.
  - A leaked link — in a shared chat, a browser history, a screenshot — goes stale within a week rather than persisting for a month.
  - **A guest who returns on day 8 has lost their trip, permanently.** There is no email to recover it with. This is a real and deliberate product cost, and it is the reason the expiry warning is a security control rather than copy: the only mitigation is converting to an account before expiry.
  - Expiry is checked **server-side against the stored record**, not by cookie `Max-Age`. A cookie lifetime is a client-side hint that an attacker replaying a captured token simply ignores.
  - The token is stored **hashed**. A leaked table of raw guest tokens would be a leaked set of live sessions.
- **Alternatives rejected:**
  - **24 hours** — tightest exposure window, but a user returning the next evening loses everything, which makes the guest mode close to unusable for its stated purpose.
  - **30 days** — most forgiving, but a bearer capability with no revocation path living for a month is an unreasonable exposure for a trip containing accessibility needs and travel dates.
- **Review trigger:** Analytics show guest sessions commonly expiring before conversion; or a guest-to-account recovery mechanism is introduced, which would change the loss calculus entirely.

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [ADR-013](ADR-013-auth0-as-identity-provider.md) — decided alongside this
- [BR-014](../product/10-logs/blast-radius/BR-014-browser-session.md) — the change that forced it
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
