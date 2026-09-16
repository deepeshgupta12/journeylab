import { expect, test } from '@playwright/test';

/**
 * Search visibility of the public coverage page — STEP-007 close (§3, §8, §26).
 *
 * WHAT THE STEP ACTUALLY ASKS FOR
 *   §3 "public coverage and SEO pages"; §8 "server-rendered for speed and SEO"; §26
 *   "SEO/CWV measurement". No document sets a numeric SEO target, and ranking cannot
 *   be measured before there is anything to rank. So this measures the properties
 *   the page itself owns and a crawler depends on, and nothing it cannot own:
 *
 *     the content is in the server HTML  -> a crawler that runs no JavaScript still
 *                                           reads the answer, which is what
 *                                           "server-rendered for SEO" means
 *     a specific title and description   -> not the shell's generic pair
 *     a declared language                -> `lang` on <html>
 *     not marked unindexable             -> no `noindex` in a meta tag or header
 *
 * DELIBERATELY `request`, NOT `page`
 *   `page` runs JavaScript, so it would pass every assertion below for a page that
 *   renders nothing until hydration — the exact failure the step's §8 rules out.
 *   The APIRequestContext fetches bytes and executes nothing, which is what a
 *   crawler without a renderer sees.
 *
 * NOT MEASURED, AND RECORDED AS SUCH
 *   There is no robots.txt and no sitemap. Neither is required by any document, so
 *   none is invented here; their absence is stated in the step's completion record.
 */

test.describe('the coverage page is legible to a crawler that runs no JavaScript', () => {
  test('the answer is in the server-rendered HTML', async ({ request }) => {
    const response = await request.get('/coverage');
    // Presence anchor first (BUG-032): every absence assertion below would pass on a 404.
    expect(response.status(), 'the coverage route must exist').toBe(200);
    expect(response.headers()['content-type'] ?? '').toContain('text/html');

    const html = await response.text();
    expect(html, 'the heading is not in the server HTML').toMatch(
      /<h1[^>]*>\s*Where JourneyLab can plan\s*<\/h1>/i,
    );
    // REQ-TRIP-001: coverage, limitations and the privacy summary before an account.
    expect(html, 'the region table is not in the server HTML').toContain(
      'Supported regions, their planning windows and known limitations',
    );
    expect(html, 'the privacy summary is not in the server HTML').toContain(
      'Planning without an account',
    );
    // STEP-007.05: how old the answer is must be readable without hydration too.
    expect(html, 'observed_at is not in the server HTML').toMatch(/data-observed-at="[^"]+"/);
  });

  test('the title and description describe this page, not the site', async ({ request }) => {
    const html = await (await request.get('/coverage')).text();
    expect(html).toMatch(/<title>Coverage (—|&#8212;|&mdash;) JourneyLab<\/title>/);
    const description = html.match(/<meta name="description" content="([^"]*)"/)?.[1] ?? '';
    expect(description, 'no meta description in the server HTML').toMatch(
      /^Which regions JourneyLab can plan/,
    );
    // Not the shell's generic description, which every page would otherwise share.
    expect(description).not.toBe('Compare feasible futures before and during travel');
  });

  test('the document declares its language', async ({ request }) => {
    const html = await (await request.get('/coverage')).text();
    expect(html).toMatch(/<html[^>]*\slang="[a-z]{2,3}(-[A-Za-z0-9]+)*"/);
  });

  test('the page is not marked unindexable', async ({ request }) => {
    const response = await request.get('/coverage');
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html, 'a robots meta tag excludes the page').not.toMatch(
      /<meta[^>]+name="robots"[^>]+content="[^"]*noindex/i,
    );
    expect(
      response.headers()['x-robots-tag'] ?? '',
      'an X-Robots-Tag header excludes the page',
    ).not.toMatch(/noindex/i);
  });
});
