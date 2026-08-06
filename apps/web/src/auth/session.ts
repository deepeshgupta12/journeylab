/**
 * Browser session — STEP-002.05 (REQ-SEC-003, REQ-PRIV-001).
 *
 * This is the file the sub-step names. It composes the pieces around it —
 * cookies, CSRF, refresh, guest capability, OIDC — into the small number of
 * decisions a request actually needs.
 *
 * TWO KINDS OF SESSION, ONE RULE
 *   An authenticated session and a guest session are different in every way that
 *   matters (one has an identity, the other is a bearer capability), so they are
 *   different types rather than one type with a nullable user. Code that handles
 *   "a session" must state which it means, and the compiler makes it.
 *
 * FAIL CLOSED
 *   Every function returning a session returns `null` on any doubt. There is no
 *   branch that produces a degraded or partially-trusted session, and in
 *   particular an identity-provider outage produces no session at all — never an
 *   anonymous-but-authorized one (sub-step §5).
 */

import {
  ALL_SESSION_COOKIES,
  type CookieSpec,
  csrfCookie,
  expireCookie,
  GUEST_COOKIE,
  REFRESH_COOKIE,
  SESSION_COOKIE,
  tokenCookie,
} from './cookies';
import { issueCsrfToken } from './csrf';
import { GUEST_SESSION_SECONDS, type GuestSession } from './guest';
import { needsRefresh, type SingleFlightRefresher, type TokenSet } from './refresh';

export interface AuthenticatedSession {
  readonly kind: 'authenticated';
  readonly subject: string;
  readonly tokens: TokenSet;
}

export interface GuestSessionState {
  readonly kind: 'guest';
  readonly token: string;
  readonly expiresAt: number;
}

export type Session = AuthenticatedSession | GuestSessionState;

/** Cookies to set when an authenticated session begins. */
export function authenticatedSessionCookies(
  tokens: TokenSet,
  now: number = Date.now(),
): CookieSpec[] {
  const accessLifetime = Math.max(1, Math.floor((tokens.expiresAt - now) / 1000));
  return [
    tokenCookie(SESSION_COOKIE, tokens.accessToken, accessLifetime),
    // The refresh cookie deliberately outlives the access token — that is its
    // purpose. It is httpOnly like the rest: a refresh token is the more valuable
    // of the two, since it mints new access tokens.
    tokenCookie(REFRESH_COOKIE, tokens.refreshToken, GUEST_SESSION_SECONDS),
    csrfCookie(issueCsrfToken(), GUEST_SESSION_SECONDS),
  ];
}

export function guestSessionCookies(guest: GuestSession): CookieSpec[] {
  return [
    tokenCookie(GUEST_COOKIE, guest.token, GUEST_SESSION_SECONDS),
    csrfCookie(issueCsrfToken(), GUEST_SESSION_SECONDS),
  ];
}

/**
 * Cookies that end a session.
 *
 * Clears every cookie in `ALL_SESSION_COOKIES` rather than the ones this session
 * happens to have used. Sign-out must not depend on correctly identifying what
 * kind of session was in play — if that inference is ever wrong, a cookie
 * survives sign-out.
 *
 * This is only the client half. Server-side revocation is authoritative and is
 * what actually ends access (sub-step §11).
 */
export function signOutCookies(): CookieSpec[] {
  return ALL_SESSION_COOKIES.map((name: string) => expireCookie(name));
}

export type SessionResolution =
  | { readonly session: Session; readonly setCookies: CookieSpec[] }
  | { readonly session: null; readonly setCookies: CookieSpec[] };

/**
 * Resolve the session for a request, refreshing if needed.
 *
 * Returns the cookies the caller must set, rather than setting them. The same
 * reasoning as `AuditRecord` in the provisioning service: handing the obligation
 * back as a value means it cannot be silently skipped, and it keeps this function
 * free of framework I/O so it can be tested directly.
 */
export async function resolveAuthenticatedSession(
  tokens: TokenSet | null,
  refresher: SingleFlightRefresher,
  sessionKey: string,
  subject: string,
  now: number = Date.now(),
): Promise<SessionResolution> {
  if (tokens === null) {
    return { session: null, setCookies: [] };
  }

  if (!needsRefresh(tokens, now)) {
    return { session: { kind: 'authenticated', subject, tokens }, setCookies: [] };
  }

  const outcome = await refresher.refresh(sessionKey, tokens.refreshToken);
  if (!outcome.ok) {
    // Provider unavailable or refresh rejected. Both end the session and clear
    // its cookies — carrying on with an expired access token would be exactly the
    // "anonymous authorized session" §5 forbids.
    return { session: null, setCookies: signOutCookies() };
  }

  return {
    session: { kind: 'authenticated', subject, tokens: outcome.tokens },
    setCookies: authenticatedSessionCookies(outcome.tokens, now),
  };
}
