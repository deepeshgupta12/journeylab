import { defineConfig } from 'vitest/config';

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
  },
});
