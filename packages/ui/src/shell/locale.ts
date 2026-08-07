/**
 * Document language and direction — STEP-003.05 (REQ-A11Y-001).
 *
 * WHY `dir` IS NOT OPTIONAL
 *   `lang` alone tells a screen reader which voice to use; `dir` tells the
 *   BROWSER which way the text runs. Omitting it on an Arabic or Hebrew page
 *   leaves punctuation, numbers and mixed Latin/RTL runs in the wrong order —
 *   text that is technically present and genuinely unreadable.
 *
 *   It is derived rather than configured because a mismatched pair (lang="ar"
 *   with dir="ltr") is worse than either alone, and that mismatch is exactly what
 *   a hand-maintained setting drifts into.
 */

/**
 * Languages written right-to-left, by ISO 639-1/2 code.
 *
 * The list is short and stable. `Intl.Locale.prototype.textInfo` would be the
 * standards answer, but it is not available in every runtime in the support
 * matrix, and falling back silently to LTR is the failure this exists to prevent.
 */
const RTL_LANGUAGES = new Set([
  'ar', // Arabic
  'arc', // Aramaic
  'dv', // Divehi
  'fa', // Persian
  'ha', // Hausa (Ajami script)
  'he', // Hebrew
  'khw', // Khowar
  'ks', // Kashmiri
  'ku', // Kurdish (Sorani)
  'ps', // Pashto
  'ur', // Urdu
  'yi', // Yiddish
]);

export type Direction = 'ltr' | 'rtl';

export interface DocumentLocale {
  readonly lang: string;
  readonly dir: Direction;
}

/**
 * Resolve `lang` and `dir` from a BCP 47 tag.
 *
 * Matches on the primary subtag, so `ar-EG` and `ar` behave identically. An
 * unrecognised tag resolves to LTR — the safe default for the overwhelming
 * majority of languages, and the wrong answer only for a language we do not yet
 * support at all.
 */
export function documentLocale(tag: string): DocumentLocale {
  const normalised = tag.trim().toLowerCase();
  if (normalised === '') {
    // An empty lang attribute is worse than a wrong one: screen readers fall back
    // to the user's system voice, which mispronounces every place name.
    return { lang: 'en', dir: 'ltr' };
  }
  const primary = normalised.split(/[-_]/)[0] ?? normalised;
  return { lang: normalised, dir: RTL_LANGUAGES.has(primary) ? 'rtl' : 'ltr' };
}

export function isRightToLeft(tag: string): boolean {
  return documentLocale(tag).dir === 'rtl';
}
