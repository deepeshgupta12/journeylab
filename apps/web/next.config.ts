import path from 'node:path';
import type { NextConfig } from 'next';

/**
 * Load the monorepo-root .env — STEP-002.05.
 *
 * Next resolves .env relative to the APP directory (apps/web), but this
 * repository keeps a single .env at the root so the API, the database tooling and
 * the web app cannot drift onto different credentials. Without this, every Auth0
 * variable is undefined here and sign-in fails with a configuration error.
 *
 * process.loadEnvFile is built into Node 22+, so this needs no dependency. It does
 * not overwrite variables already set, so real environment variables (CI,
 * production) still win over the file.
 */
const rootEnv = path.resolve(import.meta.dirname, '../../.env');
try {
  process.loadEnvFile(rootEnv);
} catch {
  // Absent .env is normal in CI and in production, where variables are injected
  // by the platform. Missing REQUIRED values are caught by auth/config.ts with a
  // message naming the variable — failing here would be less useful.
}

const nextConfig: NextConfig = {
  // The workspace root, not apps/web — otherwise Next infers it from the lockfile
  // and warns on every start.
  outputFileTracingRoot: path.resolve(import.meta.dirname, '../..'),

  typescript: {
    /*
     * BUG-017 — this does NOT skip type checking. It makes the build SAY SO.
     *
     * `next build` runs its own type check by loading the TypeScript compiler
     * API from `typescript/lib/typescript.js`. TypeScript 7 (ADR-009) is the
     * native compiler: its package ships `tsc.js`, `getExePath.js` and
     * `version.cjs`, and no JavaScript API entry at all. Next therefore decides
     * TypeScript is "not installed" — and under `CI=true` it refuses to
     * auto-install and aborts the build with the word `Failed` and nothing else.
     *
     * The other half of the fix is the `@typescript/native-preview`
     * devDependency; see the note beside it in package.json.
     *
     * With that marker present Next skips its own check, and the flag below
     * decides what it says about having done so. Left at `false` the build
     * prints "Running TypeScript … Finished TypeScript in 75ms" while checking
     * NOTHING — a green message for work that did not happen, which is the most
     * expensive kind of wrong. `true` prints "Skipping validation of types",
     * which is true.
     *
     * Types ARE checked, by `pnpm typecheck` — `tsc --noEmit` against this
     * package's own tsconfig, proven non-vacuous by injecting a type error and
     * observing TS2322.
     *
     * Revisit when Next recognises `typescript@7` directly.
     */
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
