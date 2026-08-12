/**
 * Browser session tests — TST-SEC-003, TST-PRIV-001 · STEP-002.05.
 *
 * Each security property here is also mutation-tested (see IMPL-012): the suite
 * is only evidence if breaking the control makes it fail.
 */

import { describe, expect, it, vi } from 'vitest';

import {
  ALL_SESSION_COOKIES,
  type CookieSpec,
  CSRF_COOKIE,
  csrfCookie,
  expireCookie,
  GUEST_COOKIE,
  REFRESH_COOKIE,
  SESSION_COOKIE,
  serializeCookie,
  tokenCookie,
} from './cookies';
import { CSRF_HEADER, isSafeMethod, issueCsrfToken, verifyCsrf } from './csrf';
import {
  GUEST_EXPIRY_WARNING_SECONDS,
  GUEST_SESSION_SECONDS,
  hashGuestToken,
  issueGuestSession,
  validateGuestSession,
} from './guest';
import {
  buildAuthorizationRequest,
  type DiscoveryDocument,
  exchangeCode,
  type OidcConfig,
  verifyCallback,
} from './oidc';
import { needsRefresh, type RefreshOutcome, SingleFlightRefresher, type TokenSet } from './refresh';
import {
  authenticatedSessionCookies,
  guestSessionCookies,
  resolveAuthenticatedSession,
  signOutCookies,
} from './session';

const NOW = 1_800_000_000_000;

function tokens(overrides: Partial<TokenSet> = {}): TokenSet {
  return {
    accessToken: 'access-token-value',
    refreshToken: 'refresh-token-value',
    expiresAt: NOW + 3_600_000,
    ...overrides,
  };
}

// --- REQ-SEC-003: tokens are never JS-readable -------------------------------

describe('cookie policy', () => {
  it('makes every token cookie httpOnly and Secure', () => {
    for (const name of [SESSION_COOKIE, REFRESH_COOKIE, GUEST_COOKIE]) {
      const spec = tokenCookie(name, 'value', 60);
      expect(spec.attributes.httpOnly, `${name} must be httpOnly`).toBe(true);
      expect(spec.attributes.secure, `${name} must be Secure`).toBe(true);
    }
  });

  it('refuses a token cookie without the __Host- prefix', () => {
    expect(() => tokenCookie('jl_session', 'v', 60)).toThrow(/__Host-/);
  });

  it('refuses a token cookie with no lifetime', () => {
    expect(() => tokenCookie(SESSION_COOKIE, 'v', 0)).toThrow(/lifetime/);
  });

  it('emits HttpOnly and Secure in the serialized header', () => {
    const header = serializeCookie(tokenCookie(SESSION_COOKIE, 'v', 60));
    expect(header).toContain('HttpOnly');
    expect(header).toContain('Secure');
    expect(header).toContain('SameSite=Lax');
    expect(header).toContain('Path=/');
  });

  it('leaves only the CSRF cookie readable by JavaScript, and it carries no token', () => {
    const csrf = csrfCookie('csrf-value', 60);
    expect(csrf.attributes.httpOnly).toBe(false);
    expect(csrf.name).toBe(CSRF_COOKIE);
    // A readable cookie is only safe if holding it grants nothing.
    expect(csrf.value).not.toContain('access');
    expect(csrf.value).not.toContain('refresh');
  });

  it('never places an access or refresh token in a JS-readable cookie', () => {
    const specs = authenticatedSessionCookies(tokens(), NOW);
    const readable = specs.filter((s) => !s.attributes.httpOnly);
    for (const spec of readable) {
      expect(spec.value).not.toBe('access-token-value');
      expect(spec.value).not.toBe('refresh-token-value');
    }
    const bearing = specs.filter(
      (s) => s.value === 'access-token-value' || s.value === 'refresh-token-value',
    );
    expect(bearing.length).toBe(2);
    for (const spec of bearing) expect(spec.attributes.httpOnly).toBe(true);
  });
});

// --- sign-out ----------------------------------------------------------------

describe('sign-out', () => {
  it('clears every known session cookie, not just the ones in use', () => {
    const cleared = new Set(signOutCookies().map((c) => c.name));
    for (const name of ALL_SESSION_COOKIES) {
      expect(cleared.has(name), `sign-out left ${name} behind`).toBe(true);
    }
  });

  it('expires cookies with Max-Age=0', () => {
    for (const spec of signOutCookies()) {
      expect(spec.attributes.maxAge).toBe(0);
      expect(spec.value).toBe('');
    }
  });

  it('expireCookie keeps httpOnly so the clear cannot be observed by script', () => {
    expect(expireCookie(SESSION_COOKIE).attributes.httpOnly).toBe(true);
  });
});

// --- REQ-PRIV-001: guest sessions, no email ----------------------------------

describe('guest session', () => {
  it('lasts exactly 7 days', () => {
    expect(GUEST_SESSION_SECONDS).toBe(7 * 24 * 60 * 60);
    const guest = issueGuestSession(NOW);
    expect(guest.expiresAt - guest.issuedAt).toBe(GUEST_SESSION_SECONDS * 1000);
  });

  it('issues an opaque token that carries no claims and is unguessable', () => {
    const a = issueGuestSession(NOW);
    const b = issueGuestSession(NOW);
    expect(a.token).not.toBe(b.token);
    expect(a.token.length).toBeGreaterThanOrEqual(40);
    expect(a.token).not.toContain('.');
  });

  it('accepts a valid unexpired token', async () => {
    const guest = issueGuestSession(NOW);
    const record = {
      tokenHash: await hashGuestToken(guest.token),
      issuedAt: guest.issuedAt,
      expiresAt: guest.expiresAt,
      revokedAt: null,
    };
    const verdict = await validateGuestSession(guest.token, record, NOW + 1000);
    expect(verdict.valid).toBe(true);
  });

  it('rejects an expired token even when the cookie would still be sent', async () => {
    const guest = issueGuestSession(NOW);
    const record = {
      tokenHash: await hashGuestToken(guest.token),
      issuedAt: guest.issuedAt,
      expiresAt: guest.expiresAt,
      revokedAt: null,
    };
    const verdict = await validateGuestSession(guest.token, record, guest.expiresAt + 1);
    expect(verdict.valid).toBe(false);
    if (!verdict.valid) expect(verdict.reason).toBe('expired');
  });

  it('rejects an unknown token rather than defaulting to allow', async () => {
    const verdict = await validateGuestSession('a'.repeat(43), undefined, NOW);
    expect(verdict.valid).toBe(false);
    if (!verdict.valid) expect(verdict.reason).toBe('unknown_token');
  });

  it('rejects a token that does not match the stored hash', async () => {
    const guest = issueGuestSession(NOW);
    const other = issueGuestSession(NOW);
    const record = {
      tokenHash: await hashGuestToken(other.token),
      issuedAt: guest.issuedAt,
      expiresAt: guest.expiresAt,
      revokedAt: null,
    };
    const verdict = await validateGuestSession(guest.token, record, NOW);
    expect(verdict.valid).toBe(false);
    if (!verdict.valid) expect(verdict.reason).toBe('unknown_token');
  });

  it('rejects a REVOKED record while it is still unexpired', async () => {
    // STEP-002.08. The whole point of the server-side store: a session ended by
    // signing out, or by an administrator, must stop working immediately rather
    // than running to its natural seven-day expiry (ADR-014).
    const guest = issueGuestSession(NOW);
    const record = {
      tokenHash: await hashGuestToken(guest.token),
      issuedAt: guest.issuedAt,
      expiresAt: guest.expiresAt,
      revokedAt: NOW + 1000,
    };
    const verdict = await validateGuestSession(guest.token, record, NOW + 2000);
    expect(verdict.valid).toBe(false);
    if (!verdict.valid) expect(verdict.reason).toBe('revoked');
  });

  it('reports revocation rather than expiry when a revoked session also expired', async () => {
    // Order matters for the audit trail, not for the outcome: both refuse. Only
    // one of them says a human deliberately ended the session.
    const guest = issueGuestSession(NOW);
    const record = {
      tokenHash: await hashGuestToken(guest.token),
      issuedAt: guest.issuedAt,
      expiresAt: guest.expiresAt,
      revokedAt: NOW + 1000,
    };
    const verdict = await validateGuestSession(guest.token, record, guest.expiresAt + 1);
    expect(verdict.valid).toBe(false);
    if (!verdict.valid) expect(verdict.reason).toBe('revoked');
  });

  it('stores a hash, never the token itself', async () => {
    const guest = issueGuestSession(NOW);
    const hash = await hashGuestToken(guest.token);
    expect(hash).not.toBe(guest.token);
    expect(await hashGuestToken(guest.token)).toBe(hash);
  });

  it('warns before expiry rather than at it', async () => {
    const guest = issueGuestSession(NOW);
    const record = {
      tokenHash: await hashGuestToken(guest.token),
      issuedAt: guest.issuedAt,
      expiresAt: guest.expiresAt,
      revokedAt: null,
    };
    const early = await validateGuestSession(guest.token, record, NOW);
    const late = await validateGuestSession(
      guest.token,
      record,
      guest.expiresAt - GUEST_EXPIRY_WARNING_SECONDS * 1000 + 1000,
    );
    expect(early.valid && early.expiringSoon).toBe(false);
    expect(late.valid && late.expiringSoon).toBe(true);
  });

  it('issues a guest session with no email anywhere in it', () => {
    const specs = guestSessionCookies(issueGuestSession(NOW));
    for (const spec of specs) expect(spec.value).not.toContain('@');
  });
});

// --- single-flight refresh ---------------------------------------------------

describe('token refresh', () => {
  it('refreshes before expiry, not at it', () => {
    const set = tokens({ expiresAt: NOW + 30_000 });
    expect(needsRefresh(set, NOW)).toBe(true);
    expect(needsRefresh(tokens({ expiresAt: NOW + 3_600_000 }), NOW)).toBe(false);
  });

  it('coalesces concurrent refreshes into ONE provider call', async () => {
    let resolveIt: ((v: RefreshOutcome) => void) | undefined;
    const gate = new Promise<RefreshOutcome>((resolve) => {
      resolveIt = resolve;
    });
    const refresher = new SingleFlightRefresher(() => gate);

    const flights = [1, 2, 3, 4, 5].map(() => refresher.refresh('session-a', 'rt'));
    resolveIt?.({ ok: true, tokens: tokens() });
    const results = await Promise.all(flights);

    expect(refresher.providerCalls).toBe(1);
    for (const result of results) expect(result.ok).toBe(true);
  });

  it('does not share a refresh between different sessions', async () => {
    const refresher = new SingleFlightRefresher(async () => ({ ok: true, tokens: tokens() }));
    await Promise.all([refresher.refresh('a', 'rt-a'), refresher.refresh('b', 'rt-b')]);
    expect(refresher.providerCalls).toBe(2);
  });

  it('does not wedge the session after a failed refresh', async () => {
    const fn = vi
      .fn<(refreshToken: string) => Promise<RefreshOutcome>>()
      .mockRejectedValueOnce(new Error('network'))
      .mockResolvedValueOnce({ ok: true, tokens: tokens() });
    const refresher = new SingleFlightRefresher(fn);

    const first = await refresher.refresh('a', 'rt');
    expect(first.ok).toBe(false);

    const second = await refresher.refresh('a', 'rt');
    expect(second.ok, 'a later refresh was blocked by the earlier failure').toBe(true);
  });

  it('fails closed when the provider throws', async () => {
    const refresher = new SingleFlightRefresher(() => {
      throw new Error('provider down');
    });
    const outcome = await refresher.refresh('a', 'rt');
    expect(outcome.ok).toBe(false);
    if (!outcome.ok) expect(outcome.reason).toBe('provider_unavailable');
  });
});

// --- fail closed -------------------------------------------------------------

describe('session resolution', () => {
  it('returns no session when there are no tokens', async () => {
    const refresher = new SingleFlightRefresher(async () => ({ ok: true, tokens: tokens() }));
    const result = await resolveAuthenticatedSession(null, refresher, 'k', 'sub', NOW);
    expect(result.session).toBeNull();
  });

  it('keeps a live session without calling the provider', async () => {
    const refresher = new SingleFlightRefresher(async () => ({ ok: true, tokens: tokens() }));
    const result = await resolveAuthenticatedSession(tokens(), refresher, 'k', 'sub', NOW);
    expect(result.session?.kind).toBe('authenticated');
    expect(refresher.providerCalls).toBe(0);
  });

  it('yields NO session when the identity provider is unavailable', async () => {
    const refresher = new SingleFlightRefresher(async () => ({
      ok: false,
      reason: 'provider_unavailable',
    }));
    const expiring = tokens({ expiresAt: NOW + 1000 });
    const result = await resolveAuthenticatedSession(expiring, refresher, 'k', 'sub', NOW);

    expect(result.session, 'an IdP outage produced an authorized session').toBeNull();
    const cleared = new Set(result.setCookies.map((c: CookieSpec) => c.name));
    for (const name of ALL_SESSION_COOKIES) expect(cleared.has(name)).toBe(true);
  });

  it('yields no session when the refresh token is rejected', async () => {
    const refresher = new SingleFlightRefresher(async () => ({
      ok: false,
      reason: 'refresh_rejected',
    }));
    const expiring = tokens({ expiresAt: NOW + 1000 });
    const result = await resolveAuthenticatedSession(expiring, refresher, 'k', 'sub', NOW);
    expect(result.session).toBeNull();
  });
});

// --- CSRF --------------------------------------------------------------------

describe('CSRF', () => {
  it('allows safe methods without a token', () => {
    for (const method of ['GET', 'HEAD', 'OPTIONS', 'TRACE', 'get']) {
      expect(isSafeMethod(method)).toBe(true);
      expect(verifyCsrf(method, undefined, undefined).allowed).toBe(true);
    }
  });

  it('denies state-changing requests with no cookie, no header, or a mismatch', () => {
    const token = issueCsrfToken();
    for (const method of ['POST', 'PUT', 'PATCH', 'DELETE']) {
      expect(verifyCsrf(method, undefined, token).allowed).toBe(false);
      expect(verifyCsrf(method, token, undefined).allowed).toBe(false);
      expect(verifyCsrf(method, token, issueCsrfToken()).allowed).toBe(false);
      expect(verifyCsrf(method, '', '').allowed).toBe(false);
      expect(verifyCsrf(method, token, token).allowed).toBe(true);
    }
  });

  it('names the header consumers must echo', () => {
    expect(CSRF_HEADER).toBe('x-jl-csrf');
  });
});

// --- OIDC / Auth0 adapter ----------------------------------------------------

const CONFIG: OidcConfig = {
  issuer: 'https://journeylab.eu.auth0.com/',
  clientId: 'client-id',
  redirectUri: 'https://localhost:5709/api/auth/callback',
  clientSecret: 'client-secret',
};

const DISCOVERY: DiscoveryDocument = {
  issuer: 'https://journeylab.eu.auth0.com/',
  authorization_endpoint: 'https://journeylab.eu.auth0.com/authorize',
  token_endpoint: 'https://journeylab.eu.auth0.com/oauth/token',
  jwks_uri: 'https://journeylab.eu.auth0.com/.well-known/jwks.json',
};

describe('OIDC authorization request', () => {
  it('uses PKCE with S256, never plain', async () => {
    const request = await buildAuthorizationRequest(CONFIG, DISCOVERY);
    const url = new URL(request.url);
    expect(url.searchParams.get('code_challenge_method')).toBe('S256');
    expect(url.searchParams.get('code_challenge')).toBeTruthy();
    expect(url.searchParams.get('code_challenge')).not.toBe(request.codeVerifier);
  });

  it('requests offline_access so a refresh token exists at all', async () => {
    const request = await buildAuthorizationRequest(CONFIG, DISCOVERY);
    const scope = new URL(request.url).searchParams.get('scope') ?? '';
    expect(scope.split(' ')).toContain('offline_access');
    expect(scope.split(' ')).toContain('openid');
  });

  it('generates a fresh state and nonce per request', async () => {
    const a = await buildAuthorizationRequest(CONFIG, DISCOVERY);
    const b = await buildAuthorizationRequest(CONFIG, DISCOVERY);
    expect(a.state).not.toBe(b.state);
    expect(a.nonce).not.toBe(b.nonce);
    expect(a.codeVerifier).not.toBe(b.codeVerifier);
  });

  it('never puts the client secret in the authorization URL', async () => {
    const request = await buildAuthorizationRequest(CONFIG, DISCOVERY);
    expect(request.url).not.toContain(CONFIG.clientSecret);
  });
});

describe('OIDC callback', () => {
  it('accepts only a matching state', () => {
    expect(verifyCallback('abc', 'abc', undefined).ok).toBe(true);
    expect(verifyCallback('abc', 'xyz', undefined).ok).toBe(false);
  });

  it('denies when state is missing on either side', () => {
    expect(verifyCallback(undefined, 'abc', undefined).ok).toBe(false);
    expect(verifyCallback('abc', undefined, undefined).ok).toBe(false);
    expect(verifyCallback(undefined, undefined, undefined).ok).toBe(false);
  });

  it('denies when the provider reports an error, before looking at state', () => {
    const verdict = verifyCallback('abc', 'abc', 'access_denied');
    expect(verdict.ok).toBe(false);
    if (!verdict.ok) expect(verdict.reason).toBe('provider_error');
  });
});

describe('code exchange', () => {
  it('returns tokens on success', async () => {
    const fetcher = async () =>
      new Response(
        JSON.stringify({
          access_token: 'at',
          refresh_token: 'rt',
          id_token: 'it',
          expires_in: 300,
        }),
        { status: 200, headers: { 'content-type': 'application/json' } },
      );
    const result = await exchangeCode(CONFIG, DISCOVERY, 'code', 'verifier', fetcher);
    expect(result?.access_token).toBe('at');
  });

  it('returns undefined — not a partial session — on a provider error', async () => {
    const fetcher = async () => new Response('nope', { status: 401 });
    expect(await exchangeCode(CONFIG, DISCOVERY, 'code', 'verifier', fetcher)).toBeUndefined();
  });

  it('returns undefined when the provider is unreachable', async () => {
    const fetcher = async () => {
      throw new Error('ECONNREFUSED');
    };
    expect(await exchangeCode(CONFIG, DISCOVERY, 'code', 'verifier', fetcher)).toBeUndefined();
  });

  it('sends the code verifier so PKCE is actually completed', async () => {
    let body = '';
    const fetcher = async (_url: string, init: RequestInit) => {
      body = String(init.body);
      return new Response(JSON.stringify({ access_token: 'at', id_token: 'it', expires_in: 300 }), {
        status: 200,
      });
    };
    await exchangeCode(CONFIG, DISCOVERY, 'the-code', 'the-verifier', fetcher);
    expect(body).toContain('code_verifier=the-verifier');
    expect(body).toContain('grant_type=authorization_code');
  });
});
