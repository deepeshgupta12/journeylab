import { cookies, headers } from 'next/headers';

import { GUEST_COOKIE, REFRESH_COOKIE, SESSION_COOKIE } from '@/auth/cookies';
import { requestI18n } from '@/lib/i18n';

/**
 * Sign-in verification page — STEP-002.05 scaffold, restyled at STEP-003.08.
 *
 * WHY IT CHANGED
 *   The first real-browser axe run failed here, and only here:
 *
 *     [serious] color-contrast — tr:nth-child(n) > td:nth-child(3)
 *
 *   The page was written with inline hex colours (`#666`, `#888`, `#e6ffed`)
 *   before the design system existed. `#888` on white is 3.5:1 — below the 4.5:1
 *   WCAG 1.4.3 requires for body text — and being inline it was invisible to
 *   `tokens.test.ts`, which computes ratios for declared token pairings only.
 *
 *   This closes the accessibility criterion STEP-002.05 recorded as unmet with
 *   the note "no UI exists — binds at STEP-003".
 *
 * WHAT IT STILL IS
 *   A diagnostic, not product UI. STEP-007 onwards builds the real surfaces. It
 *   reads cookies SERVER-side, which is the only way to observe an httpOnly
 *   cookie at all — and is why a client-side check could never confirm the
 *   session exists.
 */

export const dynamic = 'force-dynamic';

export default async function Home({ searchParams }: { searchParams: Promise<{ auth?: string }> }) {
  const { auth } = await searchParams;
  const jar = await cookies();
  const head = await headers();
  const { t } = requestI18n(head.get('accept-language'));

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
    <>
      <h1>{t('home.title')} — sign-in verification</h1>
      <p className="jl-page__lede">
        STEP-002.05 scaffold. Not product UI — the real surfaces begin at STEP-007.
      </p>

      <table className="jl-table">
        {/* A caption, not a heading beside it: a caption is announced when a
            screen reader enters the table. Same rule the DataTable enforces. */}
        <caption>Session cookie state</caption>
        <thead>
          <tr>
            <th scope="col">Present</th>
            <th scope="col">Check</th>
            <th scope="col">Detail</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, value, detail]) => (
            <tr key={label}>
              {/* The tick is decorative; the text beside it carries the state,
                  so this is never colour or glyph alone (REQ-A11Y-004). */}
              <td>
                <span aria-hidden="true">{value ? '✓' : '—'}</span>
                <span className="jl-visually-hidden">{value ? 'yes' : 'no'}</span>
              </td>
              <td>{label}</td>
              <td>
                <code>{detail}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {sessionEstablished && (
        <div className="jl-state jl-page__result jl-page__result--ok">
          <p className="jl-state__label">{t('home.sessionEstablished')}</p>
          <p className="jl-state__detail">
            The cookies above are httpOnly, so no script on this page can read them — including this
            one. It sees them only because it runs on the server.
          </p>
        </div>
      )}

      {silentFailure && (
        <div className="jl-state jl-page__result jl-page__result--warn">
          <p className="jl-state__label">
            Auth0 succeeded but no session cookie reached this request.
          </p>
          <p className="jl-state__detail">
            These cookies use the <code>__Host-</code> prefix, which requires HTTPS and the{' '}
            <code>Secure</code> attribute. Most likely causes: the request came from a tool with no
            cookie jar (curl), or the browser is on a different origin than the one that set them.
            If the address bar says &ldquo;Not Secure&rdquo;, run <code>mkcert -install</code>,
            enter your password, then fully quit and reopen the browser.
          </p>
        </div>
      )}

      <nav aria-label="Diagnostics" className="jl-page__links">
        <p>
          protocol: {proto} · <a href="/api/auth/login">sign in</a> ·{' '}
          <a href="/api/auth/session">session JSON</a> · <a href="/api/health">health</a>
        </p>
      </nav>
    </>
  );
}
