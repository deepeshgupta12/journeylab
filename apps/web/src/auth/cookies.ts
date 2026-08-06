/**
 * Session cookie policy — STEP-002.05 (REQ-SEC-003).
 *
 * THE ONE RULE
 *   A token never becomes readable by JavaScript. `httpOnly` is not a hardening
 *   option here, it is the control: an XSS bug should cost a defaced page, not
 *   every session on the origin. There is deliberately no helper in this module
 *   that writes a token to a JS-visible cookie or to `localStorage`, so a caller
 *   in a hurry has nothing convenient to reach for.
 *
 * FRONTEND_ARCHITECTURE §6 requires SameSite cookies plus a per-request token on
 * state-changing calls. Both live here and in `csrf.ts`.
 */

/** Cookie names. Prefixed so they cannot be set by a subdomain over plain HTTP. */
export const SESSION_COOKIE = '__Host-jl_session';
export const REFRESH_COOKIE = '__Host-jl_refresh';
export const GUEST_COOKIE = '__Host-jl_guest';
export const CSRF_COOKIE = '__Host-jl_csrf';

/**
 * `__Host-` is not decoration. It forces Secure, forbids Domain, and pins Path=/,
 * which is what stops a compromised sibling subdomain from planting a session
 * cookie on this origin. The browser enforces it; we cannot get it wrong later.
 */
const HOST_PREFIX = '__Host-';

export interface CookieAttributes {
  readonly httpOnly: boolean;
  readonly secure: boolean;
  readonly sameSite: 'strict' | 'lax' | 'none';
  readonly path: string;
  readonly maxAge: number;
}

export interface CookieSpec {
  readonly name: string;
  readonly value: string;
  readonly attributes: CookieAttributes;
}

/**
 * Attributes for a token-bearing cookie.
 *
 * `sameSite: "lax"` rather than `"strict"`: a strict session cookie is not sent on
 * the top-level navigation back from the identity provider, so the user lands
 * signed-out immediately after signing in. Lax still blocks cross-site
 * subrequests, and CSRF is covered separately by a per-request token rather than
 * being left to SameSite alone.
 */
export function tokenCookie(name: string, value: string, maxAgeSeconds: number): CookieSpec {
  if (!name.startsWith(HOST_PREFIX)) {
    throw new Error(`token cookie ${name} must use the ${HOST_PREFIX} prefix`);
  }
  if (maxAgeSeconds <= 0) {
    throw new Error('token cookie needs a positive lifetime; use expireCookie() to clear one');
  }
  return {
    name,
    value,
    attributes: {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/',
      maxAge: maxAgeSeconds,
    },
  };
}

/**
 * The CSRF cookie is the one cookie that is deliberately readable by JavaScript.
 *
 * That is the double-submit pattern: the client must echo the value in a header,
 * which a cross-site attacker cannot do because it cannot read the cookie. It
 * carries no authority on its own — holding it grants nothing.
 */
export function csrfCookie(value: string, maxAgeSeconds: number): CookieSpec {
  return {
    name: CSRF_COOKIE,
    value,
    attributes: {
      httpOnly: false,
      secure: true,
      sameSite: 'lax',
      path: '/',
      maxAge: maxAgeSeconds,
    },
  };
}

/** Clear a cookie. maxAge 0 rather than a past date: no clock comparison to get wrong. */
export function expireCookie(name: string): CookieSpec {
  return {
    name,
    value: '',
    attributes: { httpOnly: true, secure: true, sameSite: 'lax', path: '/', maxAge: 0 },
  };
}

/** Every cookie sign-out must clear. Enumerated so a new cookie cannot be forgotten. */
export const ALL_SESSION_COOKIES = [
  SESSION_COOKIE,
  REFRESH_COOKIE,
  GUEST_COOKIE,
  CSRF_COOKIE,
] as const;

export function serializeCookie(spec: CookieSpec): string {
  const parts = [`${spec.name}=${spec.value}`, `Path=${spec.attributes.path}`];
  parts.push(`Max-Age=${spec.attributes.maxAge}`);
  parts.push(`SameSite=${cap(spec.attributes.sameSite)}`);
  if (spec.attributes.secure) parts.push('Secure');
  if (spec.attributes.httpOnly) parts.push('HttpOnly');
  return parts.join('; ');
}

function cap(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
