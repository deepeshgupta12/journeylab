import { defineConfig, devices } from '@playwright/test';

/**
 * Real-browser accessibility harness — STEP-003.08.
 *
 * WHY A SECOND TEST RUNNER
 *   The 256 component tests run in jsdom, which has no layout engine, no paint
 *   and no forced-colors mode. Everything those tests assert about geometry,
 *   visibility or contrast is therefore an assertion about a document that was
 *   never laid out. Six criteria carried forward from STEP-003.01–.07 for exactly
 *   that reason; this is where they are settled.
 *
 * PRODUCTION BUILD, NOT DEV SERVER
 *   `pnpm build && pnpm start`, not `next dev`. A development build ships extra
 *   instrumentation, unminified bundles and no static optimisation, so its Core
 *   Web Vitals describe software nobody runs. It also hydrates differently, which
 *   is the one thing STEP-003.07's locale decision was designed around.
 *
 * PORT 5708, not 5709. 5709 is the developer's HTTPS dev server; a test run that
 * seized it would either fail or — worse — silently test whatever was already
 * listening there.
 */

const PORT = 5708;

/**
 * The API application. 5710 extends the reserved block by one, approved by the
 * owner at STEP-007.02 — 5700-5707 are infrastructure, 5708 is this harness and
 * 5709 is the developer's HTTPS dev server, so the block was full.
 */
const API_PORT = 5710;

export default defineConfig({
  testDir: './src/test',
  // A11y failures must be reproducible, not "flaky". No retries: a retry policy
  // on an accessibility gate is a way of not fixing accessibility.
  retries: 0,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : [['list']],

  /*
   * CONCURRENCY AND BUDGETS ARE CAPPED IN CI, FOR THE SAME REASON VITEST'S ARE.
   *
   * Playwright defaults to one worker per two CPUs, and each worker drives a
   * Chromium instance. `pnpm ci:local` runs in a container Docker gives 4 GB —
   * the same ceiling that broke the jsdom suites — and there the desktop project
   * timed out on six tests while the mobile project passed, which is the
   * signature of contention rather than of a broken page.
   *
   * The timeout rises with it. axe walks the entire accessibility tree of the
   * gallery, which is the largest page in the product by some distance; 30s is
   * generous on a developer machine and tight on a shared runner with two
   * browsers competing for it.
   *
   * This is a budget for the ENVIRONMENT, not for the product. The Core Web
   * Vitals assertions inside the suite are unchanged and still gate at 2.5s LCP
   * and 200ms interaction — a slow runner may not finish the suite quickly, but
   * it may not report a slow page as acceptable.
   */
  ...(process.env.CI ? { workers: 2 } : {}),
  timeout: process.env.CI ? 90_000 : 30_000,
  expect: { timeout: process.env.CI ? 20_000 : 10_000 },

  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    // A real phone profile: 44x44 touch targets and the 48rem breakpoint are
    // meaningless assertions at 1280px wide.
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],

  /*
   * TWO SERVERS, BECAUSE THE COVERAGE PAGE HAS A DATA SOURCE — STEP-007.02.
   *
   * The page reads `API-017` over HTTP rather than querying Postgres, because
   * ADR-003 declares one deployable API application and duplicating the
   * aggregate-health rule in TypeScript is how BUG-029 happened between a
   * projection and a contract.
   *
   * So the accessibility run needs the API up. If it fails to start, these tests
   * fail — which is correct: a coverage page rendered against no data would pass
   * axe and prove nothing about the surface being shipped.
   */
  webServer: [
    {
      command: `uv run uvicorn --app-dir ../../apps/api/src app:app --host 127.0.0.1 --port ${API_PORT}`,
      url: `http://127.0.0.1:${API_PORT}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        JOURNEYLAB_DATABASE_URL:
          process.env.JOURNEYLAB_DATABASE_URL ??
          'postgresql://journeylab:journeylab_dev_only@127.0.0.1:5700/journeylab',
      },
    },
    {
      command: `next start --port ${PORT}`,
      url: `http://127.0.0.1:${PORT}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        JOURNEYLAB_API_URL: `http://127.0.0.1:${API_PORT}`,
        // The gallery is off by default; the accessibility run is the one caller
        // that turns it on. See src/app/dev/gallery/gate.ts.
        JOURNEYLAB_ENABLE_GALLERY: '1',
        // next start refuses to boot without these; the a11y run never signs in.
        AUTH0_ISSUER: process.env.AUTH0_ISSUER ?? 'https://a11y.invalid/',
        AUTH0_CLIENT_ID: process.env.AUTH0_CLIENT_ID ?? 'a11y',
        AUTH0_CLIENT_SECRET: process.env.AUTH0_CLIENT_SECRET ?? 'a11y',
        AUTH0_REDIRECT_URI: process.env.AUTH0_REDIRECT_URI ?? 'https://a11y.invalid/cb',
      },
    },
  ],
});
