import { defineConfig } from 'vitest/config';

/**
 * Design-system test configuration.
 *
 * CONCURRENCY IS CAPPED IN CI, AND THAT IS A MEMORY DECISION
 *   Vitest defaults to one worker per CPU. Every worker in this package builds
 *   its own jsdom and loads axe-core into it, which is the heaviest pair of
 *   dependencies in the repository — so eight workers means eight jsdoms.
 *
 *   `pnpm ci:local` runs in a container Docker gives 4 GB. Under that ceiling the
 *   workers thrash, the main thread cannot answer their transform requests, and
 *   seven of eight suites die with:
 *
 *     [vitest-worker]: Timeout calling "fetch" with "[...test.tsx","web"]"
 *
 *   That message names no file of ours and looks like a module-resolution
 *   failure. It is memory exhaustion.
 *
 *   Capping at two workers is not a workaround for a slow machine: a suite that
 *   only passes with several gigabytes free is fragile everywhere, and a CI
 *   runner is always a shared, constrained machine. Locally the cap does not
 *   apply, so the fast path stays fast.
 */
export default defineConfig({
  test: {
    // jsdom is required for the component and axe tests. Token tests are pure and
    // unaffected by it.
    environment: 'jsdom',
    globals: false,
    /*
     * Spread rather than `maxWorkers: CI ? 2 : undefined`.
     *
     * `exactOptionalPropertyTypes` is on (tsconfig.base.json), so an optional
     * property may be absent but may not be explicitly `undefined`. The ternary
     * typechecks fine to the eye and fails with TS2769 — and `vitest run` never
     * typechecks its own config, so only `pnpm typecheck` catches it.
     */
    ...(process.env.CI ? { maxWorkers: 2, minWorkers: 1 } : {}),
    // The default 5s is a transform budget, not a test budget. A cold container
    // transforming a 300-line TSX file with esbuild can exceed it on first touch
    // while being perfectly healthy.
    testTimeout: process.env.CI ? 30_000 : 10_000,
    hookTimeout: process.env.CI ? 30_000 : 10_000,
  },
  esbuild: { jsx: 'automatic' },
});
