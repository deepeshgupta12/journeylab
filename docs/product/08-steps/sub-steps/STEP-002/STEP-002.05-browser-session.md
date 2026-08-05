---
sub_step_id: STEP-002.05
parent_step: STEP-002
title: Browser session, token refresh and guest sessions
status: NOT_STARTED
owners: []
requirement_ids: [REQ-SEC-003, REQ-PRIV-001]
blast_radius_id: BR-011
depends_on: [STEP-002.04]
last_updated: 2026-08-05
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
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015; KG-Q-014 (token storage and transport) |
| Direct dependents | Every authenticated route |
| Unknown / low-confidence areas | Guest-session recovery — losing the token loses the trip; the UX warning is a product decision |
| Blast radius | BR-011 — HIGH (credential handling in the browser) |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [ ] Server-side session helpers; tokens in **httpOnly, SameSite cookies** — never `localStorage`
- [ ] Silent refresh with a single-flight guard against refresh storms
- [ ] Guest session: opaque, expiring, bearer-capability token with a clear expiry warning
- [ ] Sign-out clears session and revokes refresh server-side
- [ ] Fail closed: IdP unavailable ⇒ no anonymous authorized session
- [ ] CSRF protection on state-changing requests

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
- [ ] Sub-step record · logs · `BR-011` · parent §21 · tracker
- [ ] [FRONTEND_ARCHITECTURE](../../../03-architecture/FRONTEND_ARCHITECTURE.md) §6 confirmed against implementation

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | | STEP-001 + 002.01–.04 |
| R7 | | Must pass |
| R2–R6 | | As applicable |

## 11. Rollback
Client session code reverts cleanly; server-side revocation remains authoritative regardless of client version.

## 12. Acceptance criteria
- [ ] Tokens are httpOnly and not JS-readable
- [ ] Refresh is silent and single-flight
- [ ] Guest planning works with no email, with expiry clearly communicated
- [ ] IdP outage fails closed
- [ ] Auth flows keyboard and screen-reader complete

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Notes / surprises | A guest token is a bearer capability — anyone holding the link holds the trip. The expiry warning is a security control, not copy |
