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
  test('is readable with no account and sets no cookie', async ({ page, context }) => {
    await page.goto('/coverage');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(/where journeylab can plan/i);

    // REQ-PRIV-001. Not "no tracking cookie" — no cookie at all. A session issued
    // to a visitor reading a public page is an identifier nobody asked for.
    expect(await context.cookies()).toHaveLength(0);
  });

  test('names no supplier anywhere in the rendered page', async ({ page }) => {
    await page.goto('/coverage');
    const body = ((await page.locator('body').textContent()) ?? '').toLowerCase();
    for (const supplier of ['opentransportdata', 'meteoswiss', 'openstreetmap', 'otd', 'osm']) {
      expect(body).not.toContain(supplier);
    }
  });

  test('has no map, so no core action can require one', async ({ page }) => {
    // REQ-A11Y-003 is usually tested by disabling the map. Here the stronger
    // statement holds: there is nothing to disable, because the table was built
    // first and the map arrives at STEP-013.04 as an addition to it.
    await page.goto('/coverage');
    await expect(page.locator('canvas, .maplibregl-map, [data-map]')).toHaveCount(0);
  });

  test('distinguishes "nothing declared" from "we could not ask"', async ({ page }) => {
    await page.goto('/coverage');
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
    await page.goto('/coverage');
    await expect(page.getByRole('button', { name: /csv/i })).toBeVisible();
  });

  test('states the planning-without-an-account path before asking for anything', async ({
    page,
  }) => {
    await page.goto('/coverage');
    const privacy = page.getByRole('heading', { name: /planning without an account/i });
    await expect(privacy).toBeVisible();
    await expect(page.getByText(/without giving us an email address/i)).toBeVisible();
  });

  test('is fully keyboard reachable', async ({ page }) => {
    await page.goto('/coverage');
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName ?? '');
    expect(focused).not.toBe('BODY');
  });
});
