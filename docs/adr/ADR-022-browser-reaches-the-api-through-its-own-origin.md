# ADR-022 — The browser reaches the API only through the page's own origin

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.

- **Date:** 2026-10-19 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- Proposed by the implementer at `BUG-038` under `ADR-007`'s propose-then-confirm rule;
  **chosen by the owner the same day** over the alternative, with both laid out.

## Context

The coverage page's two interactive features — the date check and the waitlist — called
the platform API **directly from the browser**, at an address baked into the bundle under
a `NEXT_PUBLIC_` variable. The page and the API live on different origins, so every
request began with a CORS preflight; the API deliberately carries no middleware and
answered it 405; the browser blocked the request. Ninety-two browser tests passed, because
not one of them submitted either form. The owner's first manual click found it
(`BUG-038`).

`FRONTEND_ARCHITECTURE` prescribed server components for reads and client islands for
interaction, and said nothing about how an island reaches the API. No document stated a
CORS policy. Meanwhile the web app already proxied `/api/auth/*` to the backend
server-side, so one pattern existed and nobody had written down that it was *the* pattern.

## Decision

**A browser never calls the platform API.** Every request a client island makes goes to a
path on the page's own origin — `/api/coverage/check`, `/api/coverage/waitlist`,
`/api/coverage/waitlist/withdraw` today — where a Next route handler forwards it to the
API from the server, exactly as `/api/auth/*` already does. The browser bundle contains no
API address; `NEXT_PUBLIC_JOURNEYLAB_API_URL` is removed and must not return.

The forwarding layer has five rules, each held by a test and a mutant (`BR-067` §5, §9):

1. Forward an **allowlist** of request headers — content type, accept, the client-minted
   `Idempotency-Key`, a correlation id — and nothing else. **Never a cookie.**
2. Preserve the upstream status, body and content type: a problem document leaves as
   `application/problem+json`.
3. Return the upstream correlation id.
4. An unreachable or timed-out upstream is a **503 problem document** in the platform's
   own shape (`platform.dependency_unavailable`), never an exception, never a 200.
5. The API base is read from the server's environment, once, in one file.

And one rule on the client side: **a 503 is "could not reach", never a refusal**, in
every flow — whichever hop produced it.

## Options considered

| Option | Why not, or why |
| --- | --- |
| Add CORS middleware to the API with a per-environment origin allowlist | Smallest diff. But it introduces an allowlist that must be kept correct in every environment, keeps the API's address baked into the browser bundle, and makes `STEP-008.01`'s guest-session cookie a **cross-origin** cookie — third-party cookie restrictions would then decide whether a guest can plan a trip |
| **Same-origin route handlers — chosen** | The pattern already exists (`/api/auth/*`); the bundle learns nothing about the API; no allowlist; the session cookie is first-party; the API need never be internet-exposed |
| A `next.config` rewrite instead of handlers | Proxies without code, but gives no control over which headers cross, cannot shape an upstream failure into the platform's problem document, and `:check`-style paths need escaping in its pattern syntax. Handlers make the five rules explicit and testable |

## Consequences

1. **Every form `STEP-008` builds inherits this.** Its sub-steps add route handlers, not
   `fetch` calls to the API, and any reviewer who sees `NEXT_PUBLIC_` beside an API path
   is looking at a defect.
2. The three handlers are **internal to the web app** and appear in no contract document,
   like `/api/auth/*`. Whether internal BFF routes should be described somewhere is an open
   question this ADR raises and does not answer.
3. `FRONTEND_ARCHITECTURE` gains the rule in its architecture table, so it is law rather
   than precedent.
4. The browser suite **submits the forms through the real proxy to the real API**, and
   owns the data it needs to do so (`BR-067` §6). The seam that was tested by nobody is
   tested by the suite.
5. A latent defect in the same components is closed with it: an API-side 503 used to
   render in the withdrawal form as *"that code does not work"*.

## Affected knowledge-graph nodes

`apps/web/src/app/coverage/planning-check.tsx` (`PlanningCheck`), `waitlist.tsx`
(`Waitlist`), `fetch-coverage.ts` (`fetchCoverage`), the new `app/api/coverage/*`
handlers, and `page.tsx` (`CoveragePage`) as their only production consumer. **The graph
could not see any of them until this change** — `RISK-018`.

## Migration

None at runtime. The two client components change the path they post to; no data, no
schema, no contract moves.

## Security and privacy implications

Narrower than before: the browser no longer knows where the API is, and the proxy's
allowlist means no cookie, authorization header or forwarding header can reach the API by
accident. The `Idempotency-Key` remains client-minted — it is a de-duplication token, not
a secret, and minting it server-side would defeat it.

## Operational implications

The API can sit behind the web tier without a public address. A 503 from the proxy and a
503 from the API carry the same document; the correlation id tells them apart in logs.

## Tests

`app/api/coverage/_proxy.test.ts` (the five rules, the three paths, and a source-level
assertion that neither client component names a host); the two component suites (relative
paths; 503 → unreachable in all three flows); `coverage.spec.ts` (both forms submitted end
to end); `tests/platform_api/test_e2e_region_tool.py` (the suite's data ownership).

## Rollback

Restore the two `NEXT_PUBLIC_` constants and the absolute URLs. The forms stop working in
every real browser again, which is the state this ADR replaces — so rollback is possible
and not a return to anything that worked.

## Review trigger

`STEP-008.01` (the first session cookie crosses this boundary), or the first environment
in which the web tier and the API are deployed to different hosts.
