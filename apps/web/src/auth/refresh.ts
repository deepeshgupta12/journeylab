/**
 * Single-flight token refresh — STEP-002.05 (REQ-SEC-003).
 *
 * THE PROBLEM THIS SOLVES
 *   Short-lived access tokens expire while a page is doing several things at
 *   once. Without coordination, every in-flight request notices the expiry and
 *   starts its own refresh. That is a refresh storm: N requests to the identity
 *   provider for one user, rate limits, and — with refresh-token rotation, which
 *   Auth0 uses — a far worse outcome. Rotation invalidates the old refresh token
 *   the moment one is redeemed, so the second concurrent refresh presents a token
 *   that has just been revoked. Auth0 treats that as replay and can revoke the
 *   whole family, signing the user out entirely.
 *
 *   So single-flight is not an optimisation here. Without it, concurrency logs
 *   users out.
 *
 * The guard is per session key, not global: two different users refreshing at the
 * same moment must not block or, worse, share a result.
 */

export interface TokenSet {
  readonly accessToken: string;
  readonly refreshToken: string;
  readonly expiresAt: number;
}

export type RefreshOutcome =
  | { readonly ok: true; readonly tokens: TokenSet }
  | { readonly ok: false; readonly reason: 'provider_unavailable' | 'refresh_rejected' };

export type RefreshFn = (refreshToken: string) => Promise<RefreshOutcome>;

/**
 * Refresh this many seconds before actual expiry.
 *
 * Refreshing exactly at expiry guarantees a race with in-flight requests that
 * were issued a moment earlier and arrive just after the token dies.
 */
export const REFRESH_SKEW_SECONDS = 60;

export function needsRefresh(tokens: TokenSet, now: number = Date.now()): boolean {
  return now >= tokens.expiresAt - REFRESH_SKEW_SECONDS * 1000;
}

/**
 * Coalesces concurrent refreshes for the same session into one provider call.
 *
 * Deliberately NOT a module-level singleton map keyed by nothing — that is the
 * ambient-state mistake `auth/context.py` avoids on the server. An instance is
 * created and owned explicitly.
 */
export class SingleFlightRefresher {
  readonly #inFlight = new Map<string, Promise<RefreshOutcome>>();
  #providerCalls = 0;

  constructor(private readonly refreshFn: RefreshFn) {}

  /** Provider calls made. Exposed so tests can assert coalescing actually happened. */
  get providerCalls(): number {
    return this.#providerCalls;
  }

  async refresh(sessionKey: string, refreshToken: string): Promise<RefreshOutcome> {
    const existing = this.#inFlight.get(sessionKey);
    if (existing !== undefined) {
      // A refresh for this session is already running. Awaiting it is the whole
      // point: the second caller must not present the same refresh token again.
      return existing;
    }

    const attempt = this.#run(refreshToken);
    this.#inFlight.set(sessionKey, attempt);
    try {
      return await attempt;
    } finally {
      // Cleared in `finally` so a rejected refresh cannot wedge the session into
      // a state where every later attempt awaits a promise that already failed.
      this.#inFlight.delete(sessionKey);
    }
  }

  async #run(refreshToken: string): Promise<RefreshOutcome> {
    this.#providerCalls += 1;
    try {
      return await this.refreshFn(refreshToken);
    } catch {
      // FAIL CLOSED. A provider outage yields no session, never a session that
      // carries on with an expired token because the refresh could not be
      // completed. Sub-step §5: "IdP unavailable => no anonymous authorized
      // session."
      return { ok: false, reason: 'provider_unavailable' };
    }
  }
}
