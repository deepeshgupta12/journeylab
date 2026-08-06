/**
 * Report session state — STEP-002.05.
 *
 * Returns whether a session exists and nothing else. No token, no subject, no
 * expiry timestamp: this endpoint is readable by any script on the page, so it
 * must not become a way to read what httpOnly cookies exist to hide.
 */

import { cookies } from 'next/headers';

import { GUEST_COOKIE, SESSION_COOKIE } from '@/auth/cookies';

export const dynamic = 'force-dynamic';

export async function GET(): Promise<Response> {
  const jar = await cookies();
  const authenticated = Boolean(jar.get(SESSION_COOKIE)?.value);
  const guest = Boolean(jar.get(GUEST_COOKIE)?.value);
  return Response.json({
    kind: authenticated ? 'authenticated' : guest ? 'guest' : 'none',
  });
}
