/**
 * OIDC adapter — STEP-002.05 (REQ-SEC-003), Auth0 per ADR-013.
 *
 * DEC-004 is now decided: Auth0. This file is the only place in the repository
 * that knows that. Everything it does is plain OIDC — discovery, authorization
 * code with PKCE, refresh-token rotation — so replacing Auth0 means replacing
 * `AUTH0_ISSUER` and this adapter, not the session layer above it.
 *
 * WHAT IS PROVEN AND WHAT IS NOT
 *   The flows here are exercised against a spec-compliant OIDC provider in tests.
 *   They have **not** been run against a live Auth0 tenant, because that needs an
 *   account and credentials this repository does not hold. Auth0-specific
 *   behaviour — passkey enrolment, tenant rate limits, the exact rotation
 *   semantics under concurrent redemption — is therefore unverified. Recorded in
 *   BR-014 §9 rather than implied to work.
 *
 * PKCE IS MANDATORY, NOT OPTIONAL
 *   Even though this is a confidential client with a secret, PKCE closes the
 *   authorization-code interception window. Auth0 supports it; there is no reason
 *   to run the flow without it.
 */

export interface OidcConfig {
  readonly issuer: string;
  readonly clientId: string;
  readonly redirectUri: string;
  /** Never reaches the browser bundle — server-side route handlers only. */
  readonly clientSecret: string;
}

export interface DiscoveryDocument {
  readonly authorization_endpoint: string;
  readonly token_endpoint: string;
  readonly jwks_uri: string;
  readonly issuer: string;
}

export interface AuthorizationRequest {
  readonly url: string;
  readonly state: string;
  readonly nonce: string;
  readonly codeVerifier: string;
}

/**
 * Scopes requested at sign-in.
 *
 * `offline_access` is what makes a refresh token available at all. `email` is
 * requested but the product must not require it — REQ-PRIV-001 guarantees a guest
 * can plan without one, and an authenticated user who withholds it still gets a
 * usable account (`users.email` is nullable, and the schema's
 * `users_identifiable_unless_guest` check is satisfied by `idp_subject` alone).
 */
export const DEFAULT_SCOPES = ['openid', 'profile', 'email', 'offline_access'] as const;

export async function buildAuthorizationRequest(
  config: OidcConfig,
  discovery: DiscoveryDocument,
): Promise<AuthorizationRequest> {
  const state = randomToken();
  const nonce = randomToken();
  const codeVerifier = randomToken(64);
  const codeChallenge = await s256(codeVerifier);

  const url = new URL(discovery.authorization_endpoint);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('client_id', config.clientId);
  url.searchParams.set('redirect_uri', config.redirectUri);
  url.searchParams.set('scope', DEFAULT_SCOPES.join(' '));
  url.searchParams.set('state', state);
  url.searchParams.set('nonce', nonce);
  url.searchParams.set('code_challenge', codeChallenge);
  url.searchParams.set('code_challenge_method', 'S256');

  return { url: url.toString(), state, nonce, codeVerifier };
}

export type CallbackVerdict =
  | { readonly ok: true }
  | {
      readonly ok: false;
      readonly reason: 'state_mismatch' | 'state_missing' | 'provider_error';
    };

/**
 * Validate the redirect back from the provider before touching the code.
 *
 * `state` is the CSRF defence for the authorization flow itself: without checking
 * it, an attacker can complete a sign-in of *their* account in the victim's
 * browser. Compared in constant time and never skipped when absent.
 */
export function verifyCallback(
  returnedState: string | undefined,
  expectedState: string | undefined,
  providerError: string | undefined,
): CallbackVerdict {
  if (providerError) {
    return { ok: false, reason: 'provider_error' };
  }
  if (!returnedState || !expectedState) {
    return { ok: false, reason: 'state_missing' };
  }
  if (!timingSafeEqual(returnedState, expectedState)) {
    return { ok: false, reason: 'state_mismatch' };
  }
  return { ok: true };
}

export interface TokenResponse {
  readonly access_token: string;
  readonly refresh_token?: string;
  readonly id_token: string;
  readonly expires_in: number;
}

export type Fetcher = (url: string, init: RequestInit) => Promise<Response>;

/**
 * Exchange an authorization code for tokens.
 *
 * Any non-2xx or transport failure returns `undefined` rather than throwing a
 * detailed error upward. The caller's only correct response to a failed exchange
 * is "no session", and an error object carrying provider detail is one careless
 * `catch` away from being rendered to the user.
 */
export async function exchangeCode(
  config: OidcConfig,
  discovery: DiscoveryDocument,
  code: string,
  codeVerifier: string,
  fetcher: Fetcher = fetch,
): Promise<TokenResponse | undefined> {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: config.clientId,
    client_secret: config.clientSecret,
    code,
    redirect_uri: config.redirectUri,
    code_verifier: codeVerifier,
  });

  try {
    const response = await fetcher(discovery.token_endpoint, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    });
    if (!response.ok) return undefined;
    return (await response.json()) as TokenResponse;
  } catch {
    return undefined;
  }
}

function randomToken(bytes = 32): string {
  const buffer = new Uint8Array(bytes);
  crypto.getRandomValues(buffer);
  return base64url(buffer);
}

async function s256(verifier: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  return base64url(new Uint8Array(digest));
}

function base64url(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
