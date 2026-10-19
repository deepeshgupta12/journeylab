/**
 * Where the API is — read on the server, once, in one file.
 *
 * BUG-038. Two client components each held their own copy of this constant under a
 * `NEXT_PUBLIC_` name, which baked the API's address into the browser bundle and sent
 * the browser straight to a different origin. The API answers no CORS preflight, so
 * neither request ever left the browser in a real session — the first human to click
 * the button found it, after 92 browser tests had not.
 *
 * SERVER CODE ONLY
 *   Imported by `fetch-coverage.ts` (a server component's data path) and by the route
 *   handlers under `app/api/coverage/`. No client component imports it, and
 *   `app/api/coverage/_proxy.test.ts` asserts that neither client component names an
 *   API host at all. The browser knows this page's origin and nothing else — which is
 *   also what `STEP-008.01`'s first-party session cookie needs (`ADR-022`).
 */

export const API_BASE = process.env.JOURNEYLAB_API_URL ?? 'http://127.0.0.1:5710';
