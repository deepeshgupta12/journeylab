import type { components } from '@journeylab/contracts';

/**
 * Reading coverage — STEP-007.02.
 *
 * OVER HTTP, NOT OUT OF POSTGRES
 *   `ADR-003` declares one deployable API application, and
 *   `tests/guards/module-boundaries.sh` already forbids `apps/web` importing
 *   `services/`. Querying the database from here would also duplicate the
 *   aggregate-health rule `REQ-EVID-006` depends on, in a second language, where
 *   the two would drift — which is exactly how `BUG-029` happened between a
 *   projection and a contract.
 *
 * THE TYPE COMES FROM THE CONTRACT
 *   `components['schemas']['Coverage']` is generated. Declaring the shape here by
 *   hand would make this file a third place the response is described.
 */

export type Coverage = components['schemas']['Coverage'];
export type CoverageRegion = Coverage['regions'][number];

/** Distinguishes "nothing is declared" from "we could not ask". */
export type CoverageResult =
  | { readonly kind: 'ok'; readonly coverage: Coverage }
  | { readonly kind: 'unavailable'; readonly reason: string };

const API_BASE = process.env.JOURNEYLAB_API_URL ?? 'http://127.0.0.1:5710';

export async function fetchCoverage(): Promise<CoverageResult> {
  try {
    const response = await fetch(`${API_BASE}/coverage`, {
      // Coverage changes when a provider's health does. The API caches for 30
      // seconds; caching again here would multiply the two windows and defeat the
      // disclosure bound REQ-EVID-006 actually constrains.
      cache: 'no-store',
      headers: { accept: 'application/json' },
    });
    if (!response.ok) {
      return { kind: 'unavailable', reason: `The coverage service returned ${response.status}.` };
    }
    return { kind: 'ok', coverage: (await response.json()) as Coverage };
  } catch {
    // The caught error is deliberately not surfaced: it carries a host and port,
    // and this string is rendered to the public.
    return { kind: 'unavailable', reason: 'The coverage service could not be reached.' };
  }
}
