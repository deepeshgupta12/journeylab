---
sub_step_id: STEP-002.05
parent_step: STEP-002
title: Browser session, token refresh and guest sessions
status: IN_PROGRESS
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-003, REQ-PRIV-001]
blast_radius_id: BR-014
depends_on: [STEP-002.04]
last_updated: 2026-08-06
---

# STEP-002.05 — Browser session, token refresh and guest sessions

## 1. Outcome
The web app holds a session securely, refreshes tokens without interrupting the user, and supports a **privacy-preserving guest session that requires no email**.

## 2. Scope and boundary
**In scope:** `apps/web/src/auth/session.ts`, server-side identity helpers, token refresh, guest session issue and expiry, sign-out.
**Not in this sub-step:** onboarding UI and consent ([STEP-008](../../STEP-008-account-consent-and-traveler-profile.md)), role-aware navigation ([STEP-003](../../STEP-003-design-system-and-application-shell.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-003 | OIDC with passkey support; short-lived tokens refreshed safely | TST-SEC-003 |
| REQ-PRIV-001 | A guest can plan without providing an email | TST-PRIV-001 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **RUNNABLE** — `impact(RequestContext, upstream, 3)` returned `epistemic: exact`, LOW, nothing modified. TypeScript coverage of the graph was unknown pre-change |
| Queries run | KG-Q-015; KG-Q-014 (token storage and transport) |
| Direct dependents | Every authenticated route |
| Unknown / low-confidence areas | **Decided:** guest lifetime is 7 days with a 24-hour warning (`ADR-014`). **Still open:** nothing has run against a live Auth0 tenant |
| Blast radius | [BR-014](../../../10-logs/blast-radius/BR-014-browser-session.md) — **HIGH** (credential handling in the browser) |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [x] `__Host-` prefixed, httpOnly, Secure cookies. **No function in the package can write a token anywhere JS-readable** — `tokenCookie()` throws without the prefix and forces httpOnly
- [x] Single-flight per session key. **Required by Auth0 rotation, not an optimisation**: concurrent refreshes look like replay and can revoke the token family
- [x] Opaque 32-byte token, hashed at rest, **7-day** expiry enforced server-side against the stored record (`ADR-014`), warned in the final 24 hours
- [~] Sign-out clears **every** cookie in `ALL_SESSION_COOKIES`. **Server-side revocation of an already-issued access token is NOT implemented** — carried to STEP-002.07
- [x] Provider outage or rejected refresh ⇒ no session and cookies cleared. Mutation-tested by making it fail open
- [x] Double-submit token; missing cookie, missing header, empty string or mismatch all deny

## 6. Contracts and schema changes
Consumes `API-001`.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-SEC-003 | e2e | Sign-in, refresh and sign-out work; tokens not in JS-readable storage |
| TST-PRIV-001 | e2e | A full plan completes with no email |
| — | security | IdP outage yields no authorized session |
| — | integration | Concurrent refreshes do not multiply |

## 8. Telemetry, security and accessibility
No tokens or PII in telemetry. **Auth flows are keyboard and screen-reader complete with errors announced** — an inaccessible sign-in blocks every downstream accessibility guarantee.

## 9. Documentation to update
- [x] Sub-step record · `IMPL-012` · `BR-014` · `ADR-013` · `ADR-014` · `DEC-004` closed · regression entry · tracker
- [x] [FRONTEND_ARCHITECTURE](../../../03-architecture/FRONTEND_ARCHITECTURE.md) §6 confirmed — SameSite cookies + per-request CSRF token, no secrets in the client bundle

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | **PASS** | 292 Python + 41 TypeScript |
| R7 | **PASS — 12/12** | Untouched by this sub-step |
| R2–R6 | **PASS / N/A** | **R4 does not count `REQ-SEC-003` as satisfied.** See [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) |

## 11. Rollback
Client session code reverts cleanly; server-side revocation remains authoritative regardless of client version.

## 12. Acceptance criteria
- [x] Tokens httpOnly and not JS-readable — asserted, and mutation-tested
- [x] Refresh silent and single-flight; coalescing proven by counting provider calls
- [x] Guest session carries no email anywhere; expiry and the 24-hour warning are computed server-side. **UI communication is STEP-003**
- [x] IdP outage fails closed
- [~] **NOT MET — no UI exists to test.** Binds at STEP-003; recorded rather than assumed

## 13. Completion record
| Field | Value |
| --- | --- |
| Status | **`IN_PROGRESS`, not `VERIFIED`** — two acceptance criteria are unmet: nothing has run against a live Auth0 tenant, and the accessibility criterion has no UI to test |
| Delivered 2026-08-06 | Cookie policy, CSRF, single-flight refresh, guest capability, OIDC/PKCE adapter, fail-closed session resolution |
| Remaining, and dependencies | Live Auth0 verification + passkey enrolment (**tenant now exists**: `journeylab-dev.eu.auth0.com`; client secret and `mkcert -install` pending); accessible sign-in UI (**STEP-003**); guest session storage and immediate token revocation (**STEP-002.07**) |
| Follow-up delivered | [BR-015](../../../10-logs/blast-radius/BR-015-local-tls-and-auth0-config.md) — local TLS via mkcert (`__Host-` cookies need HTTPS, so without it the whole session layer was untestable locally), Auth0 config wiring, and a guard rule that fails on tracked key material |
| Implementation | [IMPL-012](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 41 TypeScript tests; 7/7 mutants killed |
| Decisions closed | [ADR-013](../../../../adr/ADR-013-auth0-as-identity-provider.md) **DEC-004 → Auth0**; [ADR-014](../../../../adr/ADR-014-guest-session-lifetime.md) guest lifetime 7 days |
| Notes / surprises | The prediction held and drove the design: expiry is enforced **server-side against the stored record**, because a cookie `Max-Age` is a hint a replaying attacker ignores. Unpredicted: **(1)** Auth0's refresh-token rotation makes single-flight refresh *mandatory* — concurrent refreshes look like replay and can revoke the whole family, so without it concurrency logs users out. **(2)** `typecheck.sh` and `module-boundaries.sh` stopped being vacuous here; typecheck immediately caught a missing `"type": "module"`, then failed for a *wrong* reason (one root config over every package) and had to be rewritten |
