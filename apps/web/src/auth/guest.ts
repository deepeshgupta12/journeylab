/**
 * Guest sessions — STEP-002.05 (REQ-PRIV-001).
 *
 * REQ-PRIV-001: a guest can plan a trip without providing an email.
 *
 * WHAT A GUEST TOKEN ACTUALLY IS
 *   The sub-step states it plainly: "a guest token is a bearer capability —
 *   anyone holding the link holds the trip. The expiry warning is a security
 *   control, not copy."
 *
 *   There is no email, so there is no recovery and no revocation channel. Losing
 *   the token loses the trip; leaking it gives the trip away. Expiry is the only
 *   control that bounds either, which is why it is enforced here rather than left
 *   to the cookie's Max-Age — a cookie lifetime is a client-side hint that an
 *   attacker replaying a captured token simply ignores.
 *
 * LIFETIME: 7 days, decided 2026-08-06 (see ADR-013).
 *   Long enough to plan a 3-7 day trip across several sittings; short enough that
 *   a leaked link goes stale quickly.
 */

export const GUEST_SESSION_SECONDS = 7 * 24 * 60 * 60;

/** Warn the user while they can still act on it, not as it expires. */
export const GUEST_EXPIRY_WARNING_SECONDS = 24 * 60 * 60;

/** Opaque token: 32 bytes of CSPRNG output, base64url. Carries no claims. */
const GUEST_TOKEN_BYTES = 32;

export interface GuestSession {
  readonly token: string;
  readonly issuedAt: number;
  readonly expiresAt: number;
}

export interface GuestSessionRecord {
  readonly tokenHash: string;
  readonly issuedAt: number;
  readonly expiresAt: number;
}

export function issueGuestSession(now: number = Date.now()): GuestSession {
  const bytes = new Uint8Array(GUEST_TOKEN_BYTES);
  crypto.getRandomValues(bytes);
  return {
    token: base64url(bytes),
    issuedAt: now,
    expiresAt: now + GUEST_SESSION_SECONDS * 1000,
  };
}

/**
 * Hash before storage. The server stores the hash, never the token.
 *
 * A guest token is a bearer capability, so a leaked database of raw guest tokens
 * would be a leaked set of live sessions. SHA-256 is sufficient here — unlike a
 * password, the token is 256 bits of CSPRNG output, so there is no dictionary to
 * attack and no need for a slow KDF.
 */
export async function hashGuestToken(token: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return base64url(new Uint8Array(digest));
}

export type GuestValidity =
  | { readonly valid: true; readonly expiresInSeconds: number; readonly expiringSoon: boolean }
  | { readonly valid: false; readonly reason: 'expired' | 'unknown_token' | 'malformed' };

/**
 * Decide whether a presented guest token is still usable.
 *
 * Server-side and time-checked. `record` is what the server holds; a caller that
 * cannot find a record must pass `undefined`, and gets `unknown_token` — never a
 * default-allow.
 */
export async function validateGuestSession(
  presentedToken: string,
  record: GuestSessionRecord | undefined,
  now: number = Date.now(),
): Promise<GuestValidity> {
  if (!presentedToken || presentedToken.length < 16) {
    return { valid: false, reason: 'malformed' };
  }
  if (record === undefined) {
    return { valid: false, reason: 'unknown_token' };
  }

  const presentedHash = await hashGuestToken(presentedToken);
  if (!timingSafeEqual(presentedHash, record.tokenHash)) {
    return { valid: false, reason: 'unknown_token' };
  }
  if (now >= record.expiresAt) {
    return { valid: false, reason: 'expired' };
  }

  const expiresInSeconds = Math.floor((record.expiresAt - now) / 1000);
  return {
    valid: true,
    expiresInSeconds,
    expiringSoon: expiresInSeconds <= GUEST_EXPIRY_WARNING_SECONDS,
  };
}

/**
 * Constant-time comparison.
 *
 * Both inputs are hashes of the same fixed length, so the early length return
 * leaks nothing an attacker does not already know. The loop then avoids the
 * character-position timing signal that `===` on strings can expose.
 */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function base64url(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
