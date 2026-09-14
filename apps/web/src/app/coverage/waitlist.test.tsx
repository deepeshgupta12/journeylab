/**
 * @vitest-environment jsdom
 *
 * Requested per file rather than per package — see `planning-check.test.tsx` and
 * `vitest.config.ts` for why a package-wide default breaks `i18n.test.ts`.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { Inspiration, Waitlist } from './waitlist';

/**
 * STEP-007.04 — consent at the point of capture (REQ-PRIV-002, REQ-PRIV-004).
 *
 * WHAT ONLY A RENDERED DOCUMENT CAN ANSWER
 *   Whether the box is ticked when the page loads. That is the entire rule, it is a
 *   property of the first paint, and no server-side test can see it. A component
 *   that shipped `defaultChecked` would pass every Python test in this repository.
 *
 *   The other assertion that needs rendering is negative: submitting without
 *   consent must make **no network call at all**. "The server would have refused
 *   it" is true and is not the point — the address would have left the browser.
 */

const TOKEN = 'K8s1_o0Wq3nR2vF7pZ4bLyX6dTgH9cJmA0eQnU5tYwI';

function respondWith(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response);
}

const JOINED = {
  purpose: 'waitlist_notification',
  basis: 'consent',
  granted_at: '2026-09-10T09:24:11Z',
  withdrawal_token: TOKEN,
};

function consentBox(): HTMLInputElement {
  return screen.getByRole('checkbox', { name: /you may email me/i }) as HTMLInputElement;
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// --- the rule this component exists for --------------------------------------

describe('consent is an action, not a default', () => {
  test('THE BOX IS NOT TICKED ON FIRST PAINT', () => {
    // REQ-PRIV-002. A pre-ticked box is not consent, and the usual way one appears
    // is a default written for convenience somewhere far from the checkbox.
    render(<Waitlist />);
    expect(consentBox().checked).toBe(false);
  });

  test('the box has no defaultChecked that a re-render could reveal', () => {
    // Belt and braces against the specific mistake: `defaultChecked` shows up on a
    // remount rather than on the first render, so asserting once can miss it.
    const { unmount } = render(<Waitlist />);
    expect(consentBox().checked).toBe(false);
    unmount();
    render(<Waitlist />);
    expect(consentBox().checked).toBe(false);
  });

  test('submitting without consent sends NOTHING to the network', async () => {
    // The address never leaves the browser. "The server would refuse it" is true
    // and is a different, weaker guarantee.
    const fetchMock = respondWith(201, JOINED);
    vi.stubGlobal('fetch', fetchMock);
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/email address/i), 'traveller@example.com');
    await user.click(screen.getByRole('button', { name: /add me to the list/i }));

    expect(fetchMock).not.toHaveBeenCalled();

    // BY TEXT, NOT BY ROLE. `role="alert"` is not unique on this surface — the
    // assertive NotificationRegion renders one that is empty until an outcome
    // lands, so `findByRole('alert')` matches two nodes and throws. The same
    // selector trap STEP-007.03 hit with `[aria-live="polite"]` and every `Field`.
    const message = await screen.findByText(/tick the box/i);
    expect(message.getAttribute('role')).toBe('alert');
  });

  test('the submit button is NOT disabled while consent is missing', () => {
    // A disabled control says nothing about why it is disabled, and on some
    // platforms leaves the tab order entirely — so the form reads as broken.
    // REQ-A11Y-001: pressing it produces a sentence instead.
    //
    // `.disabled`, not `toBeDisabled()`: jest-dom is not installed in this package
    // and a matcher that does not exist fails as "Invalid Chai property", which
    // reads like a product failure.
    render(<Waitlist />);
    const submit = screen.getByRole('button', { name: /add me to the list/i });
    expect((submit as HTMLButtonElement).disabled).toBe(false);
  });

  test('ticking the box sends granted true and the single purpose', async () => {
    const fetchMock = respondWith(201, JOINED);
    vi.stubGlobal('fetch', fetchMock);
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/email address/i), 'traveller@example.com');
    await user.click(consentBox());
    await user.click(screen.getByRole('button', { name: /add me to the list/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/waitlist$/);
    const body = JSON.parse(String(init.body));
    expect(body.consent).toEqual({ purpose: 'waitlist_notification', granted: true });
    expect(body.email).toBe('traveller@example.com');
  });

  test('an idempotency key is sent, and a different one each time', async () => {
    const fetchMock = respondWith(201, JOINED);
    vi.stubGlobal('fetch', fetchMock);
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/email address/i), 'a@example.com');
    await user.click(consentBox());
    await user.click(screen.getByRole('button', { name: /add me to the list/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    // Destructured with the tuple cast the other call-site assertions use.
    // Indexing twice (`calls[0][1]`) is `possibly undefined` under this config,
    // and `tsc` is right: a zero-call mock would make the assertion below throw a
    // TypeError rather than report which header was missing.
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers['Idempotency-Key']).toMatch(/^waitlist-/);
  });
});

// --- what happens after it is recorded ---------------------------------------

describe('after joining', () => {
  test('the withdrawal token is shown, with the fact that it is shown once', async () => {
    const fetchMock = respondWith(201, JOINED);
    vi.stubGlobal('fetch', fetchMock);
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/email address/i), 'traveller@example.com');
    await user.click(consentBox());
    await user.click(screen.getByRole('button', { name: /add me to the list/i }));

    expect(await screen.findByText(TOKEN)).toBeTruthy();
    // Told, not merely given. A code presented without the warning is a code
    // somebody closes the tab on.
    expect(screen.getByText(/shown once/i)).toBeTruthy();
  });

  test('the address is cleared from the form once it has been sent', async () => {
    vi.stubGlobal('fetch', respondWith(201, JOINED));
    const user = userEvent.setup();

    render(<Waitlist />);
    const field = screen.getByLabelText(/email address/i) as HTMLInputElement;
    await user.type(field, 'traveller@example.com');
    await user.click(consentBox());
    await user.click(screen.getByRole('button', { name: /add me to the list/i }));

    await waitFor(() => expect(field.value).toBe(''));
    // And the box resets, so a second person at the same browser starts from
    // un-consented rather than inheriting the first one's decision.
    expect(consentBox().checked).toBe(false);
  });

  test('a refusal is announced assertively and shows the server sentence', async () => {
    vi.stubGlobal(
      'fetch',
      respondWith(400, {
        code: 'validation.invalid_request',
        detail: 'A waitlist entry requires consent to be contacted for that purpose.',
      }),
    );
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/email address/i), 'traveller@example.com');
    await user.click(consentBox());
    await user.click(screen.getByRole('button', { name: /add me to the list/i }));

    expect(await screen.findByText(/requires consent to be contacted/i)).toBeTruthy();
  });

  test('an unreachable service says nothing was stored, and names no host', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 127.0.0.1:5710')),
    );
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/email address/i), 'traveller@example.com');
    await user.click(consentBox());
    await user.click(screen.getByRole('button', { name: /add me to the list/i }));

    expect(await screen.findByText(/nothing has been stored/i)).toBeTruthy();
    // The caught error carries a host and a port; this is rendered to the public.
    expect(document.body.textContent).not.toContain('127.0.0.1');
    expect(document.body.textContent).not.toContain('ECONNREFUSED');
  });
});

// --- withdrawal ---------------------------------------------------------------

describe('withdrawal', () => {
  test('posts the token and confirms the address was deleted', async () => {
    const fetchMock = respondWith(200, {
      purpose: 'waitlist_notification',
      withdrawn_at: '2026-09-11T18:02:44Z',
    });
    vi.stubGlobal('fetch', fetchMock);
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/withdrawal code/i), TOKEN);
    await user.click(screen.getByRole('button', { name: /remove me/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/waitlist:withdraw$/);
    expect(JSON.parse(String(init.body))).toEqual({ withdrawal_token: TOKEN });

    expect(await screen.findByText(/your address has been deleted/i)).toBeTruthy();
  });

  test('a rejected code does not say whether it ever existed', async () => {
    // The server answers 404 for both cases on purpose. A page that helpfully
    // distinguished them would undo that at the last step.
    vi.stubGlobal('fetch', respondWith(404, { code: 'authz.forbidden' }));
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.type(screen.getByLabelText(/withdrawal code/i), 'not-a-real-code');
    await user.click(screen.getByRole('button', { name: /remove me/i }));

    const message = await screen.findByText(/cannot tell you whether/i);
    expect(message).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/already been used\b(?!.*or)/i);
  });

  test('an empty code sends nothing', async () => {
    const fetchMock = respondWith(200, {});
    vi.stubGlobal('fetch', fetchMock);
    const user = userEvent.setup();

    render(<Waitlist />);
    await user.click(screen.getByRole('button', { name: /remove me/i }));
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

// --- inspiration must not read as a promise -----------------------------------

describe('inspiration', () => {
  test('states the limitation before anything else', () => {
    // The sub-step's own risk note: "Showing a beautiful page for a place we cannot
    // plan may read as a promise." A caveat placed after the encouragement is a
    // caveat that has already been skipped.
    render(<Inspiration />);
    const text = document.body.textContent ?? '';
    const caveat = text.search(/cannot plan a trip here yet/i);
    expect(caveat).toBeGreaterThanOrEqual(0);
    expect(caveat).toBeLessThan(text.search(/what we would need/i));
  });

  test('promises no date and no plan', () => {
    render(<Inspiration />);
    const text = (document.body.textContent ?? '').toLowerCase();
    for (const promise of ['coming soon', 'launching', 'next month', 'shortly we will']) {
      expect(text).not.toContain(promise);
    }
  });

  test('names no specific place it cannot cite', () => {
    // ENH-007: no real provider data has ever entered the pipeline, so anything
    // specific here would be written from memory and presented as research.
    render(<Inspiration />);
    expect(screen.queryByRole('img')).toBeNull();
  });
});
