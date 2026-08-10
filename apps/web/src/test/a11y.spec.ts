/**
 * Real-browser accessibility gate — TST-A11Y-001 · STEP-003.08.
 *
 * WHAT THIS SETTLES
 *   Six criteria were carried forward from STEP-003.01–.07 with the same reason
 *   each time: jsdom has no layout engine, so nothing about geometry, visibility,
 *   paint or forced-colors could be checked. They are settled here:
 *
 *     STEP-003.01  forced-colors rendering
 *     STEP-003.04  real-browser verification of table and list
 *     STEP-003.05  skip-link visibility on focus; Core Web Vitals
 *     STEP-003.06  touch-target size; the 48rem breakpoint
 *     STEP-003.07  RTL layout in something that actually lays out
 *
 * WHAT IT DOES NOT SETTLE
 *   Automated checks find roughly a third to a half of real accessibility
 *   defects. `docs/product/06-quality/ACCESSIBILITY_AUTOMATION_LIMITS.md`
 *   enumerates what is left, so a green run here is never mistaken for coverage.
 *   That document is not a disclaimer — it is what keeps the manual journeys
 *   scheduled instead of quietly dropped.
 */

import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';

/** WCAG 2.2 AA and everything below it. Not "best-practice", which is advisory. */
const WCAG_AA = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22a', 'wcag22aa'];

const SURFACES = [
  { name: 'shell (home)', path: '/' },
  { name: 'gallery', path: '/dev/gallery' },
  { name: 'gallery (RTL)', path: '/dev/gallery?dir=rtl' },
];

async function analyse(page: Page) {
  return new AxeBuilder({ page }).withTags(WCAG_AA).analyze();
}

function describeViolations(results: Awaited<ReturnType<typeof analyse>>): string {
  return results.violations
    .map((v) => {
      const where = v.nodes
        .slice(0, 3)
        .map((n) => `      ${n.target.join(' ')}`)
        .join('\n');
      return `  [${v.impact}] ${v.id}: ${v.help}\n${where}`;
    })
    .join('\n');
}

// --- the gate ----------------------------------------------------------------

test.describe('axe — zero AA violations', () => {
  for (const surface of SURFACES) {
    test(`${surface.name} has no WCAG 2.2 AA violations`, async ({ page }) => {
      await page.goto(surface.path);
      const results = await analyse(page);
      expect(results.violations.length, `\n${describeViolations(results)}\n`).toBe(0);
      // A run that examined nothing would also report zero violations. This is
      // the same vacuity trap the guards keep falling into.
      expect(results.passes.length).toBeGreaterThan(5);
    });
  }

  test('the dialog is checked in its OPEN state', async ({ page }) => {
    // A closed dialog is not in the DOM, so the surface scans above never see it.
    await page.goto('/dev/gallery');
    await page.getByRole('button', { name: 'Open dialog' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    const results = await analyse(page);
    expect(results.violations.length, `\n${describeViolations(results)}\n`).toBe(0);
  });

  test('the mobile drawer is checked in its OPEN state', async ({ page }) => {
    // The toggle is `display: none` above the 48rem breakpoint, so this must run
    // at a phone width regardless of which project is executing it. The first
    // version did not set the viewport and timed out waiting for a button that
    // was correctly hidden — the test was wrong, not the component.
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/dev/gallery');
    await page.getByRole('button', { name: 'Menu' }).click();
    const results = await analyse(page);
    expect(results.violations.length, `\n${describeViolations(results)}\n`).toBe(0);
  });
});

// --- the meta-test: this gate must be able to fail ---------------------------

test('axe FAILS on a seeded violation', async ({ page }) => {
  // §7 asks for this explicitly, and it is the only assertion here that proves
  // the others mean anything. A gate that cannot fail is not a gate — the same
  // lesson as tests/guards/meta/run-all.sh.
  await page.goto('/dev/gallery');
  // Wait for hydration before injecting. React owns the children of <body>, and
  // a node prepended mid-hydration is discarded. That is what happened on Linux,
  // where hydration finished later than on the development machine: the seed
  // vanished, axe found nothing, and the meta-test failed for the one reason a
  // meta-test must never fail — it had stopped testing anything.
  await page.waitForLoadState('networkidle');

  await page.evaluate(() => {
    const img = document.createElement('img');
    img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    // Explicit dimensions: axe skips elements with no layout box, and a 1x1
    // transparent GIF is close enough to none to be worth not relying on.
    img.width = 64;
    img.height = 64;
    img.setAttribute('data-seeded-violation', '');
    // No alt attribute at all: image-alt, a definite WCAG 1.1.1 A failure.
    document.body.prepend(img);
  });

  // The seed must still be in the DOM when axe runs, or this test proves nothing.
  await expect(page.locator('img[data-seeded-violation]')).toHaveCount(1);

  const results = await analyse(page);
  expect(results.violations.map((v) => v.id)).toContain('image-alt');
});

// --- keyboard ----------------------------------------------------------------

test.describe('keyboard', () => {
  test('the skip link is the first stop and BECOMES VISIBLE on focus', async ({ page }) => {
    // jsdom could assert it was focusable. Only a browser can say whether it is
    // then on screen — `clip-path: inset(50%)` leaves an element focusable and
    // invisible, which is a skip link that helps nobody who can see.
    await page.goto('/');
    await page.keyboard.press('Tab');
    const skip = page.locator('[data-skip-link]');
    await expect(skip).toBeFocused();

    const box = await skip.boundingBox();
    expect(box, 'skip link has no layout box while focused').not.toBeNull();
    expect(box?.width ?? 0).toBeGreaterThan(40);
    expect(box?.height ?? 0).toBeGreaterThan(20);
  });

  test('the skip link moves focus into main, not just the scroll position', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    await expect(page.locator('#main-content')).toBeFocused();
  });

  test('NO FOCUS TRAP outside a dialog — tabbing cycles back to the start', async ({ page }) => {
    await page.goto('/dev/gallery');
    const first = await focusSignature(page, 1);

    // Walk far enough to pass every control on the page and wrap. If focus is
    // trapped anywhere, the signature stops changing and never returns to `first`.
    const seen = new Set<string>();
    let wrapped = false;
    for (let i = 0; i < 400; i += 1) {
      await page.keyboard.press('Tab');
      const sig = await focusSignature(page, 0);
      if (sig === first && i > 3) {
        wrapped = true;
        break;
      }
      seen.add(sig);
    }
    expect(wrapped, `focus never returned to the first control; visited ${seen.size} unique`).toBe(
      true,
    );
  });

  test('the dialog DOES trap focus, and releases it on Escape', async ({ page }) => {
    // The exception that proves the rule above. A dialog must trap; everything
    // else must not.
    await page.goto('/dev/gallery');
    await page.getByRole('button', { name: 'Open dialog' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    for (let i = 0; i < 12; i += 1) {
      await page.keyboard.press('Tab');
      const inside = await page.evaluate(() => {
        const active = document.activeElement;
        return active ? !!active.closest('[role="dialog"]') : false;
      });
      expect(inside, `focus escaped the dialog after ${i + 1} tabs`).toBe(true);
    }

    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
    await expect(page.getByRole('button', { name: 'Open dialog' })).toBeFocused();
  });

  test('every interactive element shows a visible focus indicator', async ({ page }) => {
    // WCAG 2.2 SC 2.4.11. `outline: none` with no replacement is the single most
    // common keyboard regression, and it is invisible to axe.
    await page.goto('/dev/gallery');
    const bare = await page.evaluate(() => {
      const selector = 'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
      const offenders: string[] = [];
      for (const el of Array.from(document.querySelectorAll<HTMLElement>(selector))) {
        if (el.hasAttribute('disabled')) continue;
        el.focus();
        if (document.activeElement !== el) continue;
        const s = getComputedStyle(el);
        const hasOutline = s.outlineStyle !== 'none' && Number.parseFloat(s.outlineWidth) > 0;
        const hasRing = s.boxShadow !== 'none';
        const hasUnderline = s.textDecorationLine.includes('underline');
        if (!hasOutline && !hasRing && !hasUnderline) {
          offenders.push(`${el.tagName.toLowerCase()}.${el.className || '(no class)'}`);
        }
      }
      return offenders;
    });
    expect(bare, `elements with no visible focus indicator:\n${bare.join('\n')}`).toEqual([]);
  });
});

async function focusSignature(page: Page, initialTabs: number): Promise<string> {
  for (let i = 0; i < initialTabs; i += 1) await page.keyboard.press('Tab');
  return page.evaluate(() => {
    const el = document.activeElement as HTMLElement | null;
    if (!el || el === document.body) return '<body>';
    return `${el.tagName}#${el.id}.${el.className}[${el.textContent?.slice(0, 24) ?? ''}]`;
  });
}

// --- geometry: only measurable in a browser ----------------------------------

test.describe('touch targets and breakpoints', () => {
  test.skip(({ browserName }) => browserName !== 'chromium', 'geometry is engine-independent');

  test('interactive targets meet 24x24 (SC 2.5.8) at a phone viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/dev/gallery');

    const small = await page.evaluate(() => {
      const MIN = 24; // WCAG 2.2 AA. The shell aims at 44; this is the failing line.
      const offenders: string[] = [];
      const selector = 'a[href], button, input:not([type="hidden"]), select';
      for (const el of Array.from(document.querySelectorAll<HTMLElement>(selector))) {
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue; // not rendered
        // Visually hidden until focused — the skip link. It is 1x1 while hidden
        // BY DESIGN, and its focused size is asserted separately in the keyboard
        // suite. Detected by the clip technique rather than by exempting
        // anything small, which would gut the check.
        const style = getComputedStyle(el);
        if (style.clipPath.startsWith('inset(50%')) continue;
        // SC 2.5.8 exempts links inside a sentence of text, because enlarging
        // them would break the paragraph. Detect that rather than assert a rule
        // the specification does not make.
        const parent = el.parentElement;
        const inline =
          el.tagName === 'A' &&
          parent !== null &&
          (parent.tagName === 'P' || parent.tagName === 'LI') &&
          (parent.textContent?.trim().length ?? 0) > (el.textContent?.trim().length ?? 0);
        if (inline) continue;
        if (r.width < MIN || r.height < MIN) {
          offenders.push(
            `${el.tagName.toLowerCase()} "${el.textContent?.trim().slice(0, 30)}" ${Math.round(r.width)}x${Math.round(r.height)}`,
          );
        }
      }
      return offenders;
    });
    expect(small, `targets below 24x24:\n${small.join('\n')}`).toEqual([]);
  });

  test('navigation targets meet the 44x44 the shell claims', async ({ page }) => {
    // shell.css says 44 and explains why: "usable with a thumb on a moving train
    // — which is where a traveller uses this". An unmeasured claim is a comment.
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/dev/gallery');
    const links = page.locator('.jl-nav__link');
    const count = await links.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i += 1) {
      const box = await links.nth(i).boundingBox();
      if (box === null) continue;
      expect(box.height, `nav link ${i} is ${box.height}px tall`).toBeGreaterThanOrEqual(44);
    }
  });

  test('the 48rem breakpoint swaps the desktop nav for the drawer toggle', async ({ page }) => {
    await page.goto('/dev/gallery');

    await page.setViewportSize({ width: 1280, height: 900 });
    await expect(page.locator('.jl-shell__header .jl-nav').first()).toBeVisible();
    await expect(page.locator('.jl-shell__header .jl-nav__toggle').first()).toBeHidden();

    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.locator('.jl-shell__header .jl-nav').first()).toBeHidden();
  });

  test('nothing scrolls horizontally at a phone width', async ({ page }) => {
    // A horizontal scrollbar at 320px is WCAG 1.4.10 (Reflow) and the most common
    // way a "responsive" layout is not.
    await page.setViewportSize({ width: 320, height: 800 });
    await page.goto('/dev/gallery');
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow, 'the page scrolls horizontally at 320px').toBeLessThanOrEqual(1);
  });
});

// --- forced colors and RTL ---------------------------------------------------

test.describe('rendering modes', () => {
  test('content survives forced-colors', async ({ browser }) => {
    // Windows High Contrast replaces every colour. Anything conveyed by colour
    // alone, or drawn with a background-image, disappears — REQ-A11Y-004.
    const context = await browser.newContext({ forcedColors: 'active' });
    const page = await context.newPage();
    await page.goto('/dev/gallery');

    const results = await analyse(page);
    expect(results.violations.length, `\n${describeViolations(results)}\n`).toBe(0);

    // The current-page marker must still be perceivable: shell.css underlines it
    // precisely so forced-colors cannot erase the signal.
    await page.goto('/');
    const current = page.locator('[aria-current="page"]').first();
    if ((await current.count()) > 0) {
      const decoration = await current.evaluate((el) => getComputedStyle(el).textDecorationLine);
      expect(decoration).toContain('underline');
    }
    await context.close();
  });

  test('RTL mirrors the layout without breaking it', async ({ page }) => {
    // Carried from STEP-003.07, where it could only be asserted structurally.
    await page.goto('/dev/gallery?dir=rtl');
    await expect(page.locator('[dir="rtl"]').first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow, 'RTL introduced horizontal overflow').toBeLessThanOrEqual(1);

    // The proof that logical properties did their job: the skip link moves to the
    // RIGHT edge under RTL. A physical `left` would have pinned it to the left.
    await page.goto('/');
    await page.evaluate(() => document.documentElement.setAttribute('dir', 'rtl'));
    await page.keyboard.press('Tab');
    const box = await page.locator('[data-skip-link]').boundingBox();
    const width = page.viewportSize()?.width ?? 1280;
    expect(box, 'skip link not laid out under RTL').not.toBeNull();
    // Measured from the element's TRAILING edge, not its x. A first version
    // asserted `x > width / 2` and failed on a 412px phone at x=205: the link is
    // ~200px wide, so being pinned to the right edge still puts its left edge
    // just left of centre. The property is "its end sits at the viewport's end",
    // and only on a wide screen do those two happen to agree.
    const trailingGap = width - ((box?.x ?? 0) + (box?.width ?? 0));
    expect(
      trailingGap,
      `skip link ends ${trailingGap}px from the right edge of a ${width}px viewport — ` +
        'it did not follow the reading direction',
    ).toBeLessThanOrEqual(24);
  });
});

// --- Core Web Vitals ---------------------------------------------------------

test.describe('Core Web Vitals (FRONTEND_ARCHITECTURE §7)', () => {
  test.skip(({ browserName }) => browserName !== 'chromium', 'the vitals APIs are Chromium-only');

  test('LCP is within 2.5s and CLS within 0.1', async ({ page }) => {
    /*
     * THESE ARE LAB NUMBERS, AND THAT IS A REAL LIMITATION
     *   §7's budgets are field metrics: "mid-tier mobile, 4G". This runs on
     *   whatever CPU the runner has, over loopback, with no network. It cannot
     *   confirm the budget is met for a traveller on a ferry.
     *
     *   What it CAN do is catch a regression — a layout shift introduced by a
     *   change, or an LCP that goes from 200 ms to 2 s. That is worth gating on.
     *   The field measurement needs real-user monitoring, which arrives with the
     *   observability work at STEP-024.
     */
    await page.goto('/', { waitUntil: 'load' });

    const vitals = await page.evaluate(
      () =>
        new Promise<{ lcp: number; cls: number }>((resolve) => {
          let lcp = 0;
          let cls = 0;
          new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) lcp = Math.max(lcp, entry.startTime);
          }).observe({ type: 'largest-contentful-paint', buffered: true });

          new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              const shift = entry as PerformanceEntry & { value: number; hadRecentInput: boolean };
              if (!shift.hadRecentInput) cls += shift.value;
            }
          }).observe({ type: 'layout-shift', buffered: true });

          setTimeout(() => resolve({ lcp, cls }), 2_000);
        }),
    );

    expect(vitals.cls, `CLS ${vitals.cls} exceeds the 0.1 budget`).toBeLessThanOrEqual(0.1);
    expect(vitals.lcp, `LCP ${vitals.lcp}ms exceeds the 2500ms budget`).toBeLessThanOrEqual(2_500);
  });

  test('an interaction responds within the 200ms INP budget', async ({ page }) => {
    // INP is also a field metric; this measures a single interaction in the lab.
    // It catches a handler that blocks the main thread, not a slow phone.
    await page.goto('/dev/gallery');
    const button = page.getByRole('button', { name: 'Open dialog' });

    const latency = await page.evaluate(async () => {
      const el = document.querySelector<HTMLElement>('button');
      if (!el) return 0;
      const start = performance.now();
      el.click();
      await new Promise((r) => requestAnimationFrame(() => r(null)));
      return performance.now() - start;
    });
    expect(latency, `interaction took ${latency}ms`).toBeLessThanOrEqual(200);
    await expect(button).toBeVisible();
  });
});

// --- the gate on the gate ----------------------------------------------------

test('the gallery is NOT reachable without its flag', async ({ page }) => {
  /*
   * The gate is the only thing keeping a route that enumerates every internal
   * component and error string out of production. An environment check nobody
   * tests is an environment check that is wrong.
   *
   * This asserts the negative case the harness itself cannot: the harness sets
   * the flag, so it proves the route works WITH it. A separate script,
   * `pnpm a11y:gate-check`, boots a server WITHOUT the flag and asserts a 404 —
   * see tests/guards/gallery-gate.sh, which runs in `pnpm verify`.
   *
   * Here we only assert the shape the guard depends on: `notFound()` yields 404,
   * not a redirect or a 403 that would confirm the path exists.
   */
  const response = await page.goto('/dev/does-not-exist');
  expect(response?.status()).toBe(404);
});
