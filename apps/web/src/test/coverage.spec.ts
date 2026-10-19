import { expect, test } from '@playwright/test';

/**
 * The region `global-setup.ts` seeds through `tools/e2e_region.py` — BUG-038. Its
 * planning window is one year back to three years forward from the day the suite
 * runs, so the dates below are computed, not written down, and do not rot.
 */
const E2E_REGION_NAME = 'E2E Bern (browser suite)';

function isoDaysFromNow(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/**
 * The public coverage page — TST-TRIP-002, TST-A11Y-002 · STEP-007.02.
 *
 * WHAT THESE ARE PROTECTING
 *   Three promises this page makes to somebody who has not signed up:
 *
 *     no account needed  -> REQ-PRIV-001. A cookie set here is an identifier
 *                           issued to a visitor who asked for nothing.
 *     no supplier named  -> REQ-EVID-006. Which provider backs a region is
 *                           commercially confidential, and quota proximity tells
 *                           an attacker when the product degrades.
 *     honest scope       -> REQ-TRIP-002. An empty table and a broken page look
 *                           identical unless the page says which it is.
 */

test.describe('coverage page', () => {
  /**
   * EVERY TEST BELOW FIRST PROVES IT IS ON THE PAGE — BUG-032's SECOND LESSON.
   *
   * When `.gitignore` silently excluded the page from its commit, CI served a 404
   * and **three of these tests passed anyway**: "names no supplier", "has no map"
   * and "is keyboard reachable" are all ABSENCE assertions, and a 404 page
   * satisfies every one of them. It has no supplier name, no map, and a focusable
   * link.
   *
   * An absence assertion needs a presence anchor, or it is satisfied by the
   * absence of the entire page. That is the same vacuous-pass shape as a drift
   * check with no baseline and a detector that only ever asserts success — it
   * reports "the bad thing is not here" about a place that is not here either.
   */
  test.beforeEach(async ({ page }) => {
    const response = await page.goto('/coverage');
    expect(response?.status(), 'the coverage route must exist').toBe(200);
    await expect(
      page.getByRole('heading', { level: 1, name: /where journeylab can plan/i }),
      'must be on the coverage page before asserting anything about it',
    ).toBeVisible();
  });

  test('is readable with no account and sets no cookie', async ({ page, context }) => {
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(/where journeylab can plan/i);

    // REQ-PRIV-001. Not "no tracking cookie" — no cookie at all. A session issued
    // to a visitor reading a public page is an identifier nobody asked for.
    expect(await context.cookies()).toHaveLength(0);
  });

  test('names no supplier anywhere in the rendered page', async ({ page }) => {
    const body = ((await page.locator('body').textContent()) ?? '').toLowerCase();
    for (const supplier of ['opentransportdata', 'meteoswiss', 'openstreetmap', 'otd', 'osm']) {
      expect(body).not.toContain(supplier);
    }
  });

  test('has no map, so no core action can require one', async ({ page }) => {
    // REQ-A11Y-003 is usually tested by disabling the map. Here the stronger
    // statement holds: there is nothing to disable, because the table was built
    // first and the map arrives at STEP-013.04 as an addition to it.
    await expect(page.locator('canvas, .maplibregl-map, [data-map]')).toHaveCount(0);
  });

  test('shows the declared region — this is the populated page, not a loading state', async ({
    page,
  }) => {
    // The suite seeds one region (global-setup.ts), so a browser now sees the page a
    // traveller would. "Could not be loaded" is the OTHER branch — a claim about us,
    // not about coverage — and must not appear here. The empty-state copy, which
    // used to be asserted only in this file against an incidentally empty database,
    // is asserted in coverage-table.test.tsx where it depends on nobody's data.
    await expect(page.getByRole('table')).toContainText(E2E_REGION_NAME);
    const body = (await page.locator('body').textContent()) ?? '';
    expect(body).not.toMatch(/could not be loaded/i);
  });

  test('offers the CSV export the table equivalence requires', async ({ page }) => {
    // REQ-A11Y-002: every visualization has a table AND a downloadable CSV. The
    // control comes from DataTable, so this asserts the page wired it, not that
    // the component works — that is covered in the design-system suite.
    await expect(page.getByRole('button', { name: /csv/i })).toBeVisible();
  });

  test('states the planning-without-an-account path before asking for anything', async ({
    page,
  }) => {
    const privacy = page.getByRole('heading', { name: /planning without an account/i });
    await expect(privacy).toBeVisible();
    await expect(page.getByText(/without giving us an email address/i)).toBeVisible();
  });

  /**
   * BUG-038 — THE FORMS ARE SUBMITTED, THROUGH THE REAL PROXY, TO THE REAL API.
   *
   * 92 browser tests passed while both forms failed in every real browser, because
   * not one of them pressed the button: this file asserted presence, names, copy and
   * keyboard reachability, and the request itself was proven only with `fetch`
   * stubbed. The test these replace said so about itself — "when the first region is
   * declared this test must be replaced by one that exercises the form, not deleted."
   * Here it is. Nothing below stubs the network.
   */
  test.describe('the date check reaches the API through this origin', () => {
    async function check(page: import('@playwright/test').Page, first: string, last: string) {
      // By role, not by label: /destination/i also matches the waitlist's free-text
      // "Which destination?" input, and strict mode rightly refuses to pick one.
      await page
        .getByRole('combobox', { name: /^destination/i })
        .selectOption({ label: E2E_REGION_NAME });
      await page.getByLabel(/first day/i).fill(first);
      await page.getByLabel(/last day/i).fill(last);
      await page.getByRole('button', { name: /check these dates/i }).click();
    }

    test('dates inside the window are accepted — and nothing is created', async ({ page }) => {
      await check(page, isoDaysFromNow(30), isoDaysFromNow(34));
      const accepted = page
        .getByRole('status')
        .filter({ hasText: /we can plan this/i })
        .first();
      await expect(accepted).toBeVisible();
      // Five days, four nights: the off-by-one lives exactly here.
      await expect(accepted).toContainText(/4 nights/);
      await expect(accepted).toContainText(/nothing has been created yet/i);
    });

    test('a two-day trip is refused, with the supported length, and no partial plan', async ({
      page,
    }) => {
      await check(page, isoDaysFromNow(30), isoDaysFromNow(31));
      const refused = page
        .getByRole('alert')
        .filter({ hasText: /we cannot plan this/i })
        .first();
      await expect(refused).toBeVisible();
      await expect(refused).toContainText(/3 to 7 days/);
      // REQ-TRIP-002: a refusal carries a sentence and the bounds, never an outline.
      const body = (await page.locator('body').textContent()) ?? '';
      expect(body).not.toMatch(/itinerary|day 1|suggested/i);
    });

    test('dates outside the window are refused, with the window', async ({ page }) => {
      await check(page, isoDaysFromNow(4 * 365 + 10), isoDaysFromNow(4 * 365 + 14));
      const refused = page
        .getByRole('alert')
        .filter({ hasText: /we cannot plan this/i })
        .first();
      await expect(refused).toBeVisible();
      await expect(refused).toContainText(/outside that window/i);
      await expect(refused).toContainText(/we can plan this region between/i);
    });
  });

  test('joining the waitlist returns a one-time code, and the code withdraws', async ({ page }) => {
    // The one browser test that writes personal data. The address is deleted by the
    // withdrawal it performs, and global-teardown.ts removes the row by its marker.
    const run = Date.now().toString(36);
    await page.getByLabel(/email address/i).fill(`e2e-${run}@example.invalid`);
    await page.getByLabel(/which destination/i).fill(`e2e-run-${run}`);
    await page.getByRole('checkbox', { name: /you may email me/i }).check();
    await page.getByRole('button', { name: /add me to the list/i }).click();

    const joined = page
      .getByRole('status')
      .filter({ hasText: /you are on the list/i })
      .first();
    await expect(joined).toBeVisible();
    const token = (await page.locator('[data-withdrawal-token]').textContent())?.trim() ?? '';
    expect(token.length).toBeGreaterThan(20);

    await page.getByLabel(/withdrawal code/i).fill(token);
    await page.getByRole('button', { name: /remove me/i }).click();
    await expect(
      page
        .getByRole('status')
        .filter({ hasText: /^removed/i })
        .first(),
    ).toBeVisible();
    await expect(page.getByText(/your address has been deleted/i)).toBeVisible();
  });

  test('the answer says when it was taken', async ({ page }) => {
    /*
     * STEP-007.05 · REQ-EVID-006, REQ-EVID-003.
     *
     * The API caches coverage for 30 seconds. The prohibition is not on caching —
     * it is on cached data being *presented as current*, so the rendered page has
     * to carry the moment the answer was read. A page that dropped `observed_at`
     * would be presenting an estimate as confirmed, and the server could do
     * nothing about it.
     */
    const stamp = page.locator('[data-observed-at]');
    await expect(stamp, 'the page does not say when the answer was taken').toHaveCount(1);

    const observed = await stamp.getAttribute('data-observed-at');
    expect(observed, 'observed_at is empty').toBeTruthy();
    expect(
      Number.isNaN(Date.parse(observed ?? '')),
      `observed_at is not a parseable instant: ${observed}`,
    ).toBe(false);

    // Machine-readable as well as legible, and it says it is not "now".
    await expect(page.locator(`time[datetime="${observed}"]`)).toHaveCount(1);
    await expect(page.getByText(/not the moment you asked for it/i)).toBeVisible();
  });

  test('the disclosure is announced ONCE, not on every render', async ({ page }) => {
    // A live region that re-announces on each render interrupts a screen-reader
    // user reading the table below it to repeat something they were already told.
    // The count is published by the component because the DOM looks identical
    // either way — an unobservable property is one nothing is checking.
    const region = page.locator('[data-health-announcement]');
    await expect(region).toHaveCount(1);
    await expect(region).toHaveAttribute('aria-live', 'polite');
    await expect(region).toHaveAttribute('data-announce-count', '1');

    // Non-empty, or "announced once" is a count of nothing.
    expect((await region.textContent())?.trim().length ?? 0).toBeGreaterThan(10);
  });

  test('the status disclosure names no supplier and counts none', async ({ page }) => {
    const status = page.locator('[data-health-announcement]');
    const text = ((await status.textContent()) ?? '').toLowerCase();
    expect(text.length, 'the status region is empty').toBeGreaterThan(10);
    for (const supplier of ['opentransportdata', 'otd', 'meteoswiss', 'openstreetmap', 'osm']) {
      expect(text).not.toContain(supplier);
    }
    // A count reveals the supply chain's size by another route.
    expect(text).not.toMatch(/\b\d+\s+(sources?|providers?|suppliers?)\b/);
  });

  test('NO consent control anywhere on the page is pre-selected', async ({ page }) => {
    /*
     * STEP-007.04 · REQ-PRIV-002. The rule is about the FIRST PAINT of a real
     * browser, which is the one place it can be checked honestly: a component test
     * renders what the test imports, and this asserts what the server actually
     * sent to a visitor who has clicked nothing.
     *
     * Every checkbox and radio, not only the waitlist one. A pre-ticked consent
     * usually arrives as a default written for convenience somewhere far from the
     * control, so naming the specific box would be checking the place the mistake
     * has already been avoided.
     */
    const controls = page.locator('input[type="checkbox"], input[type="radio"]');

    // THE PRESENCE ANCHOR. Every assertion below is over a set that is empty when
    // the form fails to render, and "no ticked boxes" is vacuously true of a page
    // with no boxes — the exact shape that let three tests pass against a 404.
    await expect(
      controls,
      'no consent control rendered, so this test would pass over nothing',
    ).not.toHaveCount(0);

    const ticked = await page.evaluate(() =>
      Array.from(
        document.querySelectorAll<HTMLInputElement>('input[type="checkbox"], input[type="radio"]'),
      )
        .filter((el) => el.checked || el.hasAttribute('checked'))
        .map((el) => el.getAttribute('aria-label') ?? el.id ?? el.name ?? '(unnamed)'),
    );

    expect(ticked, `pre-selected consent controls: ${ticked.join(', ')}`).toEqual([]);
  });

  test('the waitlist says what the permission covers before asking for it', async ({ page }) => {
    // REQ-PRIV-002 is "specific and informed", not merely "opt-in". A tick box with
    // no statement of scope is opt-in to something unstated.
    await expect(page.getByRole('heading', { name: /tell me when this changes/i })).toBeVisible();
    await expect(page.getByText(/covers that message and nothing else/i)).toBeVisible();
    await expect(page.getByText(/withdraw it at any time/i)).toBeVisible();
    // BUG-036 / DEC-012: how long the address is kept is part of what is consented to.
    await expect(page.getByText(/after 12 months/i)).toBeVisible();
  });

  test('inspiration content does not read as a promise', async ({ page }) => {
    // The sub-step's own risk: a beautiful page for a place we cannot plan reads as
    // a commitment. The caveat must be on the page, and no date may be implied.
    await expect(page.getByText(/cannot plan a trip here yet/i)).toBeVisible();
    const body = ((await page.locator('body').textContent()) ?? '').toLowerCase();
    for (const promise of ['coming soon', 'launching', 'next month']) {
      expect(body, `the page implies a date: "${promise}"`).not.toContain(promise);
    }
  });

  test('is fully keyboard reachable', async ({ page }) => {
    /*
     * THIS TEST USED TO BE ONE TAB AND `not.toBe('BODY')` — AND BUG-033 WALKED
     * STRAIGHT PAST IT.
     *
     * "Something received focus" is not "the content is reachable". At a phone
     * viewport the right-hand 56px of this very table could be reached by pointer
     * and by no key at all, while this assertion stayed green: the skip link
     * focused, so something was not BODY. It is the same vacuity as the absence
     * assertions above, which a 404 satisfied.
     *
     * The tab order is now enumerated and the controls that must be in it are
     * named. Whether a key actually MOVES the scroll region is geometry, so it is
     * settled in a browser at the phone profile in a11y.spec.ts rather than
     * claimed here.
     */
    const order: string[] = [];
    for (let i = 0; i < 40; i += 1) {
      await page.keyboard.press('Tab');
      const signature = await page.evaluate(() => {
        const el = document.activeElement as HTMLElement | null;
        if (!el || el === document.body) return '<body>';
        const label = el.getAttribute('aria-labelledby')
          ? 'labelled'
          : (el.textContent?.trim().slice(0, 20) ?? '');
        return `${el.tagName.toLowerCase()}|${el.className}|${label}`;
      });
      if (signature === '<body>') break;
      if (order.includes(signature)) break; // wrapped
      order.push(signature);
    }

    expect(order.length, 'nothing is in the tab order').toBeGreaterThan(1);
    expect(
      order.some((s) => s.includes('jl-table__scroll')),
      `the table's scroll region is not in the tab order:\n${order.join('\n')}`,
    ).toBe(true);
    expect(
      order.some((s) => s.includes('jl-table__export')),
      `the CSV control is not in the tab order:\n${order.join('\n')}`,
    ).toBe(true);
  });
});
