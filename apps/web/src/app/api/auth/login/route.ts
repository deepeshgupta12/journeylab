/**
 * Begin sign-in — STEP-002.05.
 *
 * Builds the authorization request and stashes the three values the callback must
 * verify against: `state` (CSRF for the flow), `nonce` (replay defence for the ID
 * token) and the PKCE `code_verifier`.
 *
 * They go in short-lived httpOnly cookies, NOT in a server-side session store,
 * because there is no session yet — that is the point of the request. httpOnly
 * matters as much here as for tokens: a script that can read the verifier can
 * complete the flow.
 */

import { NextResponse } from 'next/server';

import { discover, loadOidcConfig } from '@/auth/config';
import { serializeCookie, tokenCookie } from '@/auth/cookies';
import { buildAuthorizationRequest } from '@/auth/oidc';

export const dynamic = 'force-dynamic';

/** The flow must complete in minutes; a stale verifier is a liability, not a convenience. */
const FLOW_TTL_SECONDS = 600;

export async function GET(): Promise<Response> {
  const config = loadOidcConfig();
  const discovery = await discover(config);
  const request = await buildAuthorizationRequest(config, discovery);

  const response = NextResponse.redirect(request.url, { status: 302 });
  for (const spec of [
    tokenCookie('__Host-jl_state', request.state, FLOW_TTL_SECONDS),
    tokenCookie('__Host-jl_nonce', request.nonce, FLOW_TTL_SECONDS),
    tokenCookie('__Host-jl_verifier', request.codeVerifier, FLOW_TTL_SECONDS),
  ]) {
    response.headers.append('set-cookie', serializeCookie(spec));
  }
  return response;
}
