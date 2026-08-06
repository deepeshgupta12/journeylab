/**
 * Complete sign-in — STEP-002.05.
 *
 * Order matters and is deliberate:
 *   1. provider error       -> stop before touching anything else
 *   2. state comparison     -> constant time; absence denies
 *   3. code exchange        -> failure yields no session, never a partial one
 *   4. session cookies      -> httpOnly, __Host-, via the tested helpers
 *   5. flow cookies cleared -> state/nonce/verifier are single-use
 *
 * Every failure lands on the same opaque redirect. A callback that reports WHY it
 * failed tells an attacker probing the flow exactly which control stopped them.
 */

import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { discover, loadOidcConfig } from '@/auth/config';
import { expireCookie, serializeCookie } from '@/auth/cookies';
import { exchangeCode, verifyCallback } from '@/auth/oidc';
import { authenticatedSessionCookies } from '@/auth/session';

export const dynamic = 'force-dynamic';

const FLOW_COOKIES = ['__Host-jl_state', '__Host-jl_nonce', '__Host-jl_verifier'] as const;

function failed(origin: string): Response {
  const response = NextResponse.redirect(`${origin}/?auth=failed`, { status: 302 });
  for (const name of FLOW_COOKIES) {
    response.headers.append('set-cookie', serializeCookie(expireCookie(name)));
  }
  return response;
}

export async function GET(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const origin = url.origin;
  const jar = await cookies();

  const verdict = verifyCallback(
    url.searchParams.get('state') ?? undefined,
    jar.get('__Host-jl_state')?.value,
    url.searchParams.get('error') ?? undefined,
  );
  if (!verdict.ok) return failed(origin);

  const code = url.searchParams.get('code');
  const verifier = jar.get('__Host-jl_verifier')?.value;
  if (!code || !verifier) return failed(origin);

  const config = loadOidcConfig();
  const discovery = await discover(config);
  const tokens = await exchangeCode(config, discovery, code, verifier);
  if (tokens === undefined) return failed(origin);

  const response = NextResponse.redirect(`${origin}/?auth=ok`, { status: 302 });
  for (const spec of authenticatedSessionCookies({
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token ?? '',
    expiresAt: Date.now() + tokens.expires_in * 1000,
  })) {
    response.headers.append('set-cookie', serializeCookie(spec));
  }
  // Single-use: leaving them set allows a replayed callback.
  for (const name of FLOW_COOKIES) {
    response.headers.append('set-cookie', serializeCookie(expireCookie(name)));
  }
  return response;
}
