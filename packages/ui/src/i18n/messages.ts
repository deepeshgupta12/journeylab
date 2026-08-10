/**
 * ICU message loading — STEP-003.07 (REQ-NFR-007).
 *
 * THE QUESTION CARRIED SINCE STEP-003.02, ANSWERED
 *   "ICU message loading strategy interacts with server components — resolve
 *   before STEP-003.07."
 *
 *   The decision: **catalogues are plain data, resolved synchronously, passed in
 *   explicitly.** No async loading inside a component, no module-level singleton,
 *   no reading the ambient locale.
 *
 *   Why each of those is rejected:
 *
 *   - **Async loading inside a component** makes every component that renders
 *     text a suspense boundary. In the App Router that turns a static page into a
 *     streamed one and gives it a loading state it did not need.
 *   - **A module-level singleton** holding "the current locale" is a global
 *     mutable on a server that handles many requests at once. Two users with
 *     different locales share it, and the loser sees the other's language. This
 *     is the same hazard as ambient tenant context in `auth/context.py`, which
 *     STEP-002.02 designed out for the same reason.
 *   - **Reading the ambient locale** produces the hydration mismatch §4 warns
 *     about: the server formats in one locale, the browser re-renders in
 *     another, React reports a mismatch and the user sees text change under them.
 *
 *   So a catalogue is loaded by the caller — a server component that already
 *   knows the request's locale — and handed down as a value.
 *
 * FALLBACK IS EXPLICIT AND LOSSY-VISIBLE
 *   A missing message returns the KEY, not an empty string. Blank text looks like
 *   a layout bug and gets triaged as one; a visible `trip.brief.title` is
 *   obviously a missing translation and reaches the right person.
 */

export type MessageCatalogue = Readonly<Record<string, string>>;

/** The locale every other falls back to. English, because the source strings are. */
export const FALLBACK_LOCALE = 'en';

export interface Translator {
  readonly locale: string;
  /** Resolve a key, interpolating `{name}` placeholders. */
  readonly t: (key: string, values?: Readonly<Record<string, string | number>>) => string;
  /** True when the key resolved from a real catalogue rather than falling back. */
  readonly has: (key: string) => boolean;
}

const PLACEHOLDER = /\{(\w+)\}/g;

export function interpolate(
  template: string,
  values: Readonly<Record<string, string | number>> = {},
): string {
  return template.replace(PLACEHOLDER, (match, name: string) => {
    const value = values[name];
    // An unresolved placeholder is left visible rather than blanked, for the same
    // reason a missing key is: `{count}` on screen is a bug report, "" is a
    // mystery.
    return value === undefined ? match : String(value);
  });
}

/**
 * Build a translator from a catalogue and its fallback.
 *
 * Both are values. Nothing is fetched, and nothing is cached in module scope.
 */
export function createTranslator(
  locale: string,
  catalogue: MessageCatalogue,
  fallback: MessageCatalogue = {},
): Translator {
  return {
    locale,
    has: (key) => key in catalogue,
    t: (key, values) => {
      const template = catalogue[key] ?? fallback[key];
      if (template === undefined) {
        // The key itself. See the module note.
        return key;
      }
      return interpolate(template, values);
    },
  };
}

/**
 * Resolve the best available locale from what the catalogue set offers.
 *
 * `en-AU` falls back to `en` before falling back to the default. Dropping
 * straight to the default would show an Australian reader French if French
 * happened to be first in the map.
 */
export function resolveLocale(
  requested: string,
  available: readonly string[],
  fallback: string = FALLBACK_LOCALE,
): string {
  const normalised = requested.toLowerCase();
  const exact = available.find((l) => l.toLowerCase() === normalised);
  if (exact) return exact;

  const primary = normalised.split('-')[0] ?? normalised;
  const byPrimary = available.find((l) => l.toLowerCase().split('-')[0] === primary);
  if (byPrimary) return byPrimary;

  return fallback;
}
