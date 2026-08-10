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

export default defineConfig({
  testDir: './src/test',
  // A11y failures must be reproducible, not "flaky". No retries: a retry policy
  // on an accessibility gate is a way of not fixing accessibility.
  retries: 0,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : [['list']],
  timeout: 30_000,
  expect: { timeout: 10_000 },

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

  webServer: {
    command: `next start --port ${PORT}`,
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
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
});
