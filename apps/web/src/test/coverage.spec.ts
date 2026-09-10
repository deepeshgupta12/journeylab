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
