/**
 * Server-only Auth0 configuration — STEP-002.05 (ADR-013).
 *
 * `import 'server-only'` is load-bearing, not decorative: it makes the build FAIL
 * if any client component ever imports this module. Without it, a single careless
 * import would bundle `AUTH0_CLIENT_SECRET` into JavaScript served to browsers,
 * and nothing else in the pipeline would object.
 *
 * FRONTEND_ARCHITECTURE §6: "No provider or model keys ever in the client bundle."
 */

import 'server-only';

import type { DiscoveryDocument, OidcConfig } from './oidc';

export class ConfigError extends Error {}

function required(name: string): string {
  const value = process.env[name];
  if (!value || value.trim() === '') {
    // Fail loudly at startup rather than producing a half-configured client that
    // fails later with an opaque provider error.
    throw new ConfigError(`${name} is not set. Copy .env.example to .env and fill it in.`);
  }
  return value.trim();
}

export function loadOidcConfig(): OidcConfig {
  const issuer = required('AUTH0_ISSUER');
  if (!issuer.startsWith('https://')) {
    throw new ConfigError('AUTH0_ISSUER must be https — an OIDC issuer over plain HTTP is unsafe.');
  }
  const redirectUri = required('AUTH0_REDIRECT_URI');
  if (!redirectUri.startsWith('https://')) {
    // Session cookies use the __Host- prefix, which browsers accept only over
    // TLS. A plain-HTTP redirect URI produces a sign-in that appears to succeed
    // and then silently has no session, which is a miserable thing to debug.
    throw new ConfigError(
      'AUTH0_REDIRECT_URI must be https — __Host- session cookies are rejected over plain HTTP. ' +
        'Run the dev server with pnpm dev:web (mkcert TLS).',
    );
  }
  return {
    issuer: issuer.endsWith('/') ? issuer : `${issuer}/`,
    clientId: required('AUTH0_CLIENT_ID'),
    clientSecret: required('AUTH0_CLIENT_SECRET'),
    redirectUri,
  };
}

let cached: DiscoveryDocument | undefined;

/**
 * Fetch and cache the OIDC discovery document.
 *
 * Cached for the process lifetime: endpoints change approximately never, and a
 * discovery request on every sign-in adds a round trip and a second thing that
 * can be down. A restart re-fetches, which is a sufficient invalidation story for
 * something this stable.
 */
export async function discover(config: OidcConfig): Promise<DiscoveryDocument> {
  if (cached !== undefined) return cached;

  const response = await fetch(`${config.issuer}.well-known/openid-configuration`, {
    // Next would otherwise cache this at the framework layer too; one cache is enough.
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new ConfigError(`OIDC discovery failed: HTTP ${response.status} from ${config.issuer}`);
  }
  const document = (await response.json()) as DiscoveryDocument;

  // The issuer in the document must match the one we asked. A mismatch means the
  // discovery response is not for the tenant we think it is.
  if (document.issuer !== config.issuer) {
    throw new ConfigError(
      `discovery issuer mismatch: expected ${config.issuer}, got ${document.issuer}`,
    );
  }

  cached = document;
  return document;
}

/** Test seam — discovery is cached for the process, so tests must be able to reset it. */
export function resetDiscoveryCache(): void {
  cached = undefined;
}
