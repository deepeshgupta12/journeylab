import { cookies, headers } from 'next/headers';

import { GUEST_COOKIE, REFRESH_COOKIE, SESSION_COOKIE } from '@/auth/cookies';

/**
 * Sign-in verification page — STEP-002.05 scaffold.
 *
 * NOT product UI. STEP-003 owns the design system and application shell; this
 * exists so the sign-in round trip has somewhere to land that states plainly
 * whether it worked, instead of a 404 that says nothing either way.
 *
 * It reads cookies SERVER-side. That is the only way to observe an httpOnly
 * cookie at all — which is the point of them, and is why a client-side check
 * could never confirm the session exists.
 */

export const dynamic = 'force-dynamic';

export default async function Home({ searchParams }: { searchParams: Promise<{ auth?: string }> }) {
  const { auth } = await searchParams;
  const jar = await cookies();
  const head = await headers();

  const hasSession = Boolean(jar.get(SESSION_COOKIE)?.value);
  const hasRefresh = Boolean(jar.get(REFRESH_COOKIE)?.value);
  const hasGuest = Boolean(jar.get(GUEST_COOKIE)?.value);
  const proto = head.get('x-forwarded-proto') ?? 'https';

  const rows: Array<[string, boolean, string]> = [
    ['Callback reported success', auth === 'ok', auth ? `?auth=${auth}` : 'not from a callback'],
    ['Session cookie present', hasSession, SESSION_COOKIE],
    ['Refresh cookie present', hasRefresh, REFRESH_COOKIE],
    ['Guest cookie present', hasGuest, GUEST_COOKIE],
  ];

  // The decisive check. __Host- cookies are rejected by browsers over plain HTTP,
  // so a callback that says "ok" while no session cookie arrived means the
  // browser silently dropped them — almost always an untrusted certificate.
  const sessionEstablished = auth === 'ok' && hasSession;
  const silentFailure = auth === 'ok' && !hasSession;

  return (
    <main style={{ fontFamily: 'ui-monospace, monospace', padding: '2rem', lineHeight: 1.6 }}>
      <h1 style={{ fontSize: '1.25rem' }}>JourneyLab — sign-in verification</h1>
      <p style={{ color: '#666' }}>
        STEP-002.05 scaffold. Not product UI — STEP-003 builds the real shell.
      </p>

      <table style={{ borderCollapse: 'collapse', marginTop: '1.5rem' }}>
        <tbody>
          {rows.map(([label, value, detail]) => (
            <tr key={label}>
              <td style={{ padding: '0.35rem 1rem 0.35rem 0' }}>{value ? '✅' : '—'}</td>
              <td style={{ padding: '0.35rem 1rem 0.35rem 0' }}>{label}</td>
              <td style={{ padding: '0.35rem 0', color: '#888' }}>{detail}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {sessionEstablished && (
        <p
          style={{ marginTop: '1.5rem', padding: '1rem', background: '#e6ffed', color: '#04260f' }}
        >
          <strong>Session established.</strong> The cookies above are httpOnly, so no script on this
          page can read them — including this one. It sees them only because it runs on the server.
        </p>
      )}

      {silentFailure && (
        <p
          style={{ marginTop: '1.5rem', padding: '1rem', background: '#fff5e6', color: '#3d2600' }}
        >
          <strong>Auth0 succeeded but no session cookie arrived.</strong> The browser dropped it.
          These cookies use the <code>__Host-</code> prefix, which browsers accept only over a
          TRUSTED TLS connection. If the address bar says &ldquo;Not Secure&rdquo;, run{' '}
          <code>mkcert -install</code> in a terminal, enter your password, then fully quit and
          reopen the browser.
        </p>
      )}

      <p style={{ marginTop: '2rem', color: '#888' }}>
        protocol: {proto} · <a href="/api/auth/login">sign in</a> ·{' '}
        <a href="/api/auth/session">session JSON</a> · <a href="/api/health">health</a>
      </p>
    </main>
  );
}
