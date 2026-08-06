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
};

export default nextConfig;
