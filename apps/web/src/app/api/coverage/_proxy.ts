import { API_BASE } from '../../coverage/api-base';

/**
 * Forward a browser request to the platform API from this page's own origin —
 * BUG-038, ADR-022.
 *
 * WHY THE BROWSER DOES NOT CALL THE API ITSELF
 *   It did, and it never worked. The page lives on one origin and the API on another;
 *   the browser sent a CORS preflight, the API — which deliberately carries no
 *   middleware — answered 405, and the browser blocked the request. The owner chose
 *   this over adding CORS to the API: `/api/auth/*` already proxies the same way, the
 *   bundle stops carrying the API's address, there is no origin allowlist to keep
 *   correct across environments, and `STEP-008.01`'s guest-session cookie stays
 *   first-party.
 *
 * WHAT CROSSES, AND WHAT DOES NOT
 *   Four request headers are forwarded, by allowlist: the content type, the accept
 *   type, the client-minted `Idempotency-Key`, and a correlation id if the browser
 *   sent one. Nothing else — in particular **no cookie**. The session infrastructure
 *   must not be able to leak toward the API by accident, and an allowlist is the only
 *   shape of rule that stays true when a new header appears.
 *
 *   The `Idempotency-Key` stays client-minted on purpose. It represents one user
 *   intent across retries; a key minted here would hand every browser retry a fresh
 *   one and defeat the thing it exists for.
 *
 * WHAT COMES BACK
 *   The upstream status, body and content type, unchanged — a problem document
 *   arrives as `application/problem+json` and leaves the same way — plus the
 *   correlation id, so a traveller's report can be matched to a log line. An
 *   unreachable or timed-out upstream becomes a 503 problem document in the
 *   platform's own shape (`platform.dependency_unavailable`), never an exception and
 *   never a 200. The client treats that status as "could not reach" rather than as a
 *   refusal, whichever hop produced it.
 */

const FORWARDED_REQUEST_HEADERS = [
  'content-type',
  'accept',
  'idempotency-key',
  'x-correlation-id',
] as const;

const RETURNED_RESPONSE_HEADERS = [
  'content-type',
  'x-correlation-id',
  'x-correlation-id-generated',
] as const;

/** Long enough for a cold database connection; short enough that a hung upstream is a 503, not a hung page. */
const UPSTREAM_TIMEOUT_MS = 10_000;

export async function forward(request: Request, upstreamPath: string): Promise<Response> {
  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value !== null) headers.set(name, value);
  }
  const body = await request.text();

  let upstream: Response;
  try {
    upstream = await fetch(`${API_BASE}${upstreamPath}`, {
      method: 'POST',
      headers,
      body,
      cache: 'no-store',
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
  } catch {
    // The caught error carries a host and a port. The document below names neither.
    return unreachable(new URL(request.url).pathname, headers.get('x-correlation-id'));
  }

  const returned = new Headers();
  for (const name of RETURNED_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value !== null) returned.set(name, value);
  }
  return new Response(await upstream.text(), { status: upstream.status, headers: returned });
}

/**
 * The platform's `platform.dependency_unavailable` problem, as `conventions/problem.py`
 * would build it: same `type` URI, same title, same status, same retryability. A
 * second shape here would be two places describing one error model, which is the
 * drift `BUG-029` cost.
 */
function unreachable(instance: string, correlationId: string | null): Response {
  const correlation_id =
    correlationId ?? `cor_${crypto.randomUUID().replace(/-/g, '').slice(0, 16)}`;
  const document = {
    type: 'https://journeylab.app/problems/platform.dependency_unavailable',
    title: 'A store the operation needs is unreachable',
    status: 503,
    code: 'platform.dependency_unavailable',
    correlation_id,
    retryable: true,
    detail: 'The coverage service could not be reached.',
    instance,
  };
  return new Response(JSON.stringify(document), {
    status: 503,
    headers: {
      'content-type': 'application/problem+json',
      'x-correlation-id': correlation_id,
      'x-correlation-id-generated': correlationId === null ? 'true' : 'false',
    },
  });
}
