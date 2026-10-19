import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { API_BASE } from '../../coverage/api-base';
import { forward } from './_proxy';
import { POST as check } from './check/route';
import { POST as join } from './waitlist/route';
import { POST as withdraw } from './waitlist/withdraw/route';

/**
 * BUG-038 — what crosses the origin boundary, and what does not.
 *
 * These run in Node, not jsdom: a route handler is server code and the Request and
 * Response here are the real ones. Each test is one of the rules `BR-067` §5 lists,
 * and §9 names the mutant that must die on it.
 */

function upstream(status: number, body: string, headers: Record<string, string> = {}) {
  return vi.fn().mockResolvedValue(new Response(body, { status, headers }));
}

function browserRequest(path: string, init: RequestInit = {}): Request {
  return new Request(`http://localhost:5709${path}`, { method: 'POST', ...init });
}

function sentRequest(fetchMock: ReturnType<typeof vi.fn>): { url: string; init: RequestInit } {
  const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
  return { url, init };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('what crosses the origin boundary', () => {
  test('forwards the body and the allowlisted headers, and NOTHING else', async () => {
    const fetchMock = upstream(201, '{"ok":true}', { 'content-type': 'application/json' });
    vi.stubGlobal('fetch', fetchMock);

    await forward(
      browserRequest('/api/coverage/waitlist', {
        headers: {
          'content-type': 'application/json',
          accept: 'application/json',
          'Idempotency-Key': 'waitlist-7f3a',
          'X-Correlation-Id': 'cor_browser0001',
          // None of these may reach the API. The cookie is the one that matters.
          cookie: 'jl_session=secret-session-value',
          authorization: 'Bearer should-not-cross',
          'x-forwarded-for': '203.0.113.9',
          'user-agent': 'a browser',
        },
        body: '{"email":"someone@example.invalid"}',
      }),
      '/waitlist',
    );

    const { url, init } = sentRequest(fetchMock);
    expect(url).toBe(`${API_BASE}/waitlist`);
    expect(init.method).toBe('POST');
    expect(init.body).toBe('{"email":"someone@example.invalid"}');

    const sent = new Headers(init.headers);
    expect(sent.get('idempotency-key')).toBe('waitlist-7f3a');
    expect(sent.get('x-correlation-id')).toBe('cor_browser0001');
    expect(sent.get('content-type')).toBe('application/json');
    expect(sent.get('accept')).toBe('application/json');
    expect(sent.has('cookie')).toBe(false);
    expect(sent.has('authorization')).toBe(false);
    expect(sent.has('x-forwarded-for')).toBe(false);
    expect(sent.has('user-agent')).toBe(false);
  });

  test('the Idempotency-Key is forwarded verbatim, never minted here', async () => {
    const fetchMock = upstream(201, '{}');
    vi.stubGlobal('fetch', fetchMock);
    await forward(
      browserRequest('/api/coverage/waitlist', {
        headers: { 'idempotency-key': 'waitlist-the-browser-chose-this' },
        body: '{}',
      }),
      '/waitlist',
    );
    expect(new Headers(sentRequest(fetchMock).init.headers).get('idempotency-key')).toBe(
      'waitlist-the-browser-chose-this',
    );
  });

  test('the upstream request carries a timeout, so a hung API is a 503 and not a hung page', async () => {
    const fetchMock = upstream(200, '{}');
    vi.stubGlobal('fetch', fetchMock);
    await forward(browserRequest('/api/coverage/check', { body: '{}' }), '/coverage:check');
    expect(sentRequest(fetchMock).init.signal).toBeInstanceOf(AbortSignal);
  });
});

describe('what comes back', () => {
  test('a refusal keeps its status, its body and its problem content-type', async () => {
    const problem =
      '{"type":"https://journeylab.app/problems/coverage.unsupported_dates","status":422,"code":"coverage.unsupported_dates","detail":"Outside the window.","retryable":false}';
    vi.stubGlobal(
      'fetch',
      upstream(422, problem, {
        'content-type': 'application/problem+json',
        'x-correlation-id': 'cor_api0000000001',
        'x-correlation-id-generated': 'true',
        // Hop-by-hop and server-identifying headers do not come back.
        server: 'uvicorn',
        'set-cookie': 'nope=1',
      }),
    );

    const response = await forward(
      browserRequest('/api/coverage/check', { body: '{}' }),
      '/coverage:check',
    );

    expect(response.status).toBe(422);
    expect(response.headers.get('content-type')).toBe('application/problem+json');
    expect(response.headers.get('x-correlation-id')).toBe('cor_api0000000001');
    expect(response.headers.get('x-correlation-id-generated')).toBe('true');
    expect(response.headers.has('server')).toBe(false);
    expect(response.headers.has('set-cookie')).toBe(false);
    expect(await response.text()).toBe(problem);
  });

  test('an acceptance keeps its 200 and its JSON', async () => {
    vi.stubGlobal('fetch', upstream(200, '{"nights":4}', { 'content-type': 'application/json' }));
    const response = await forward(
      browserRequest('/api/coverage/check', { body: '{}' }),
      '/coverage:check',
    );
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ nights: 4 });
  });

  test('an unreachable upstream is a 503 problem document, not an exception and not a 200', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 127.0.0.1:5710')),
    );

    const response = await forward(
      browserRequest('/api/coverage/check', { body: '{}' }),
      '/coverage:check',
    );

    expect(response.status).toBe(503);
    expect(response.headers.get('content-type')).toBe('application/problem+json');
    const document = await response.json();
    // The platform's own shape for this condition — `conventions/problem.py`.
    expect(document).toMatchObject({
      type: 'https://journeylab.app/problems/platform.dependency_unavailable',
      code: 'platform.dependency_unavailable',
      status: 503,
      retryable: true,
      instance: '/api/coverage/check',
    });
    expect(document.correlation_id).toMatch(/^cor_[0-9a-f]{16}$/);
    expect(response.headers.get('x-correlation-id')).toBe(document.correlation_id);
    expect(response.headers.get('x-correlation-id-generated')).toBe('true');
    // The error named a host and a port. The document names neither.
    expect(JSON.stringify(document)).not.toMatch(/127\.0\.0\.1|5710|ECONNREFUSED/);
  });

  test('when the browser sent a correlation id, the 503 keeps it', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('down')));
    const response = await forward(
      browserRequest('/api/coverage/check', {
        headers: { 'x-correlation-id': 'cor_browser0000002' },
        body: '{}',
      }),
      '/coverage:check',
    );
    expect(response.headers.get('x-correlation-id')).toBe('cor_browser0000002');
    expect(response.headers.get('x-correlation-id-generated')).toBe('false');
  });
});

describe('the three routes map to the three operations', () => {
  test.each([
    ['check', check, '/api/coverage/check', '/coverage:check'],
    ['waitlist', join, '/api/coverage/waitlist', '/waitlist'],
    ['waitlist/withdraw', withdraw, '/api/coverage/waitlist/withdraw', '/waitlist:withdraw'],
  ])('%s forwards to %s', async (_name, handler, ownPath, upstreamPath) => {
    const fetchMock = upstream(200, '{}');
    vi.stubGlobal('fetch', fetchMock);
    await handler(browserRequest(ownPath, { body: '{}' }));
    expect(sentRequest(fetchMock).url).toBe(`${API_BASE}${upstreamPath}`);
  });
});

describe('the browser bundle does not know where the API is', () => {
  // Read as source, the way `i18n.test.ts` reads its own file. A client component
  // that re-grew an absolute URL would compile, pass its own tests (fetch is
  // stubbed there) and fail only in a real browser — which is how BUG-038 shipped.
  test.each(['planning-check.tsx', 'waitlist.tsx'])('%s names no API host', (file) => {
    const source = readFileSync(
      fileURLToPath(new URL(`../../coverage/${file}`, import.meta.url)),
      'utf8',
    );
    expect(source).not.toMatch(/NEXT_PUBLIC_JOURNEYLAB_API_URL/);
    expect(source).not.toMatch(/127\.0\.0\.1|localhost|:5710/);
    expect(source).toMatch(/fetch\('\/api\/coverage\//);
  });
});
