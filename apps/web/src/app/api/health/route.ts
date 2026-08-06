/**
 * Liveness probe — STEP-002.05 scaffold only.
 *
 * The Next.js dev server needs at least one route to start, and without one the
 * HTTPS setup that `__Host-` cookies depend on cannot be verified at all. This is
 * that route and nothing more: no product API lives here (`STEP-004` owns those),
 * and no UI (`STEP-003` owns that).
 *
 * It deliberately reports whether the request arrived over TLS, because that is
 * the precondition for every session cookie this app sets.
 */

export const dynamic = 'force-dynamic';

export function GET(request: Request): Response {
  const secure = new URL(request.url).protocol === 'https:';
  return Response.json(
    { status: 'ok', secure, cookiePolicy: secure ? '__Host- usable' : '__Host- WILL BE REJECTED' },
    { status: 200 },
  );
}
