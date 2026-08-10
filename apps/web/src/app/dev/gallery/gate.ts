import 'server-only';

/**
 * The gallery gate — STEP-003.08.
 *
 * WHY A GALLERY EXISTS AT ALL
 *   The sub-step asks for "axe over every component story and the shell". There
 *   is no Storybook in this repository, so there is nothing called a story. The
 *   gallery is that surface: one route that renders every primitive in every
 *   quality state, so a real browser can walk it.
 *
 *   It is also the first place the design system can actually be LOOKED AT.
 *   Seven sub-steps have produced components that only jsdom has ever rendered.
 *
 * WHY IT IS GATED, AND WHY BY AN EXPLICIT FLAG
 *   A route that enumerates every internal component is a small but real
 *   information-disclosure surface in production: it names internal states,
 *   error copy and route structure to anyone who guesses the path.
 *
 *   `NODE_ENV !== 'production'` would be the obvious gate and is the wrong one
 *   here — the accessibility run has to walk this page in a PRODUCTION build,
 *   because that is the build whose Core Web Vitals and hydration behaviour are
 *   worth measuring. A gate that forces a development build would mean measuring
 *   something we never ship.
 *
 *   So the gate is an explicit opt-in variable, default off. CI sets it; a
 *   deployment does not. Unlike an implicit environment check, this one is
 *   TESTABLE: `a11y.spec.ts` asserts the route 404s when the flag is absent.
 */

export const GALLERY_FLAG = 'JOURNEYLAB_ENABLE_GALLERY';

/**
 * True only when the flag is exactly `1`.
 *
 * Not "truthy". `JOURNEYLAB_ENABLE_GALLERY=false` and
 * `JOURNEYLAB_ENABLE_GALLERY=0` are both attempts to turn it OFF, and both are
 * truthy strings in JavaScript. Accepting anything non-empty is how a flag ends
 * up enabled in production by someone who thought they had disabled it.
 */
export function galleryEnabled(env: NodeJS.ProcessEnv = process.env): boolean {
  return env[GALLERY_FLAG] === '1';
}
