/**
 * CSRF protection — STEP-002.05 (FRONTEND_ARCHITECTURE §6).
 *
 * WHY SAMESITE IS NOT ENOUGH ON ITS OWN
 *   `cookies.ts` sets SameSite=Lax, not Strict, because a Strict session cookie is
 *   withheld on the top-level navigation back from the identity provider and the
 *   user lands signed out. Lax blocks cross-site subrequests but still permits
 *   top-level cross-site GETs, and it is a browser-version-dependent defence.
 *
 *   So state-changing requests carry a per-request token as well. Two independent
 *   controls, and neither is load-bearing alone.
 *
 * Double-submit: the token is in a JS-readable cookie AND must be echoed in a
 * header. A cross-site attacker can cause the cookie to be sent but cannot read it
 * to set the header, because the same-origin policy stops them.
 */

export const CSRF_HEADER = 'x-jl-csrf';
const TOKEN_BYTES = 32;

/** Methods that may not change state, per RFC 9110. Everything else is guarded. */
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);

export function isSafeMethod(method: string): boolean {
  return SAFE_METHODS.has(method.toUpperCase());
}

export function issueCsrfToken(): string {
  const bytes = new Uint8Array(TOKEN_BYTES);
  crypto.getRandomValues(bytes);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export type CsrfVerdict =
  | { readonly allowed: true; readonly reason: 'safe_method' | 'token_matched' }
  | {
      readonly allowed: false;
      readonly reason: 'missing_cookie' | 'missing_header' | 'token_mismatch';
    };

/**
 * Decide whether a request may proceed.
 *
 * Every branch that is not an explicit match denies. A missing cookie, a missing
 * header, an empty string on either side, or a mismatch all land in the same
 * place — there is no path where absence is treated as permission.
 */
export function verifyCsrf(
  method: string,
  cookieToken: string | undefined,
  headerToken: string | undefined,
): CsrfVerdict {
  if (isSafeMethod(method)) {
    return { allowed: true, reason: 'safe_method' };
  }
  if (!cookieToken) {
    return { allowed: false, reason: 'missing_cookie' };
  }
  if (!headerToken) {
    return { allowed: false, reason: 'missing_header' };
  }
  if (!timingSafeEqual(cookieToken, headerToken)) {
    return { allowed: false, reason: 'token_mismatch' };
  }
  return { allowed: true, reason: 'token_matched' };
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
