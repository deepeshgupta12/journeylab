import { defineConfig } from 'vitest/config';

/**
 * Web application test configuration.
 *
 * THE DEFAULT ENVIRONMENT STAYS `node`, AND THAT IS A FIX, NOT A PREFERENCE
 *   STEP-007.03 needed a DOM for one component test and the first attempt set
 *   `environment: 'jsdom'` here, for the whole package. It broke `i18n.test.ts`:
 *   under jsdom `import.meta.url` is an `http://localhost/` URL rather than a
 *   `file:` one, so its `readFileSync(new URL('./i18n.ts', import.meta.url))`
 *   died with "The URL must be of scheme file".
 *
 *   That test reads its own source to prove the locale never reaches a module
 *   specifier — a security property — and a package-wide default turned it off
 *   while looking like configuration. `planning-check.test.tsx` therefore carries
 *   `@vitest-environment jsdom` in its own docblock: the file that needs a
 *   document asks for one, and no other file changes behaviour.
 *
 * THE WORKER CAP IS COPIED FROM packages/ui DELIBERATELY
 *   Same reason, same container: every jsdom worker is expensive, and
 *   `pnpm ci:local` runs under a 4 GB ceiling where eight of them thrash and fail
 *   with a message that names no file of ours.
 */
export default defineConfig({
  test: {
    globals: false,
    /*
     * `src/test/` holds the Playwright accessibility specs and must be excluded.
     *
     * Vitest's default include is `**\/*.{test,spec}.*`, which matches
     * `a11y.spec.ts`. Without this exclusion vitest imports `@playwright/test`
     * outside a Playwright runner and dies with an error about test.describe —
     * a confusing failure in the wrong suite about a file that is fine.
     */
    exclude: ['**/node_modules/**', '**/dist/**', '**/.next/**', 'src/test/**'],
    // Spread rather than a ternary: `exactOptionalPropertyTypes` refuses an
    // explicit `undefined` for an optional property, and `vitest run` never
    // typechecks its own config, so only `pnpm typecheck` would catch it.
    ...(process.env.CI ? { maxWorkers: 2, minWorkers: 1 } : {}),
    testTimeout: process.env.CI ? 30_000 : 10_000,
    hookTimeout: process.env.CI ? 30_000 : 10_000,
  },
  esbuild: { jsx: 'automatic' },
});
