import { expect, test } from '@playwright/test';

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

  test('distinguishes "nothing declared" from "we could not ask"', async ({ page }) => {
    const body = (await page.locator('body').textContent()) ?? '';

    // No region is declared yet (017 seeds none deliberately), so the empty state
    // is what renders — and it must say the emptiness is about declarations, not
    // about a failure, or it reads as "we support nowhere".
    expect(body).toMatch(/no region has been declared yet/i);
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

  test('offers no date form while nothing is declared, and says why', async ({ page }) => {
    // STEP-007.03. A form over an empty region list is a control that cannot
    // produce an answer, which reads as broken rather than as honest — the same
    // distinction the empty table draws two tests above.
    //
    // This asserts the CURRENT product state. When the first region is declared
    // this test must be replaced by one that exercises the form, not deleted:
    // a page offering no way to check dates is only correct while there is
    // nothing to check.
    await expect(page.getByRole('heading', { name: /check your dates/i })).toBeVisible();
    await expect(page.getByText(/there is nothing to check yet/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /check these dates/i })).toHaveCount(0);
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
