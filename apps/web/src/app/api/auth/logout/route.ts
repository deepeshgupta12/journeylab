/**
 * Sign out — STEP-002.05.
 *
 * POST, not GET: sign-out changes state, so it must not be triggerable by an
 * <img> tag or a prefetch. CSRF is enforced with the double-submit token.
 *
 * Clears every known cookie locally, then redirects to the provider so the
 * session ends there too. Local clearing alone leaves the user silently
 * re-authenticated on the next sign-in attempt.
 */

import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { loadOidcConfig } from '@/auth/config';
import { CSRF_COOKIE, serializeCookie } from '@/auth/cookies';
import { CSRF_HEADER, verifyCsrf } from '@/auth/csrf';
import { signOutCookies } from '@/auth/session';

export const dynamic = 'force-dynamic';

export async function POST(request: Request): Promise<Response> {
  const jar = await cookies();
  const verdict = verifyCsrf(
    'POST',
    jar.get(CSRF_COOKIE)?.value,
    request.headers.get(CSRF_HEADER) ?? undefined,
  );
  if (!verdict.allowed) {
    return Response.json({ error: 'not_found' }, { status: 404 });
  }

  const config = loadOidcConfig();
  const origin = new URL(request.url).origin;
  const providerLogout = new URL(`${config.issuer}v2/logout`);
  providerLogout.searchParams.set('client_id', config.clientId);
  providerLogout.searchParams.set('returnTo', origin);

  const response = NextResponse.redirect(providerLogout.toString(), { status: 302 });
  for (const spec of signOutCookies()) {
    response.headers.append('set-cookie', serializeCookie(spec));
  }
  return response;
}
