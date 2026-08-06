/**
 * Locale-aware numeric entry — STEP-003.02.
 *
 * WHY `Number.parseFloat` IS WRONG HERE
 *   `Number.parseFloat("1.234,56")` returns **1.234**. It stops at the comma and
 *   silently returns a plausible number that is off by three orders of magnitude.
 *   A German user typing a budget of 1.234,56 EUR would have 1.23 EUR recorded, and
 *   nothing would look broken until the itinerary was priced.
 *
 *   So separators are derived from the locale via `Intl.NumberFormat` rather than
 *   assumed, and anything ambiguous is REJECTED rather than guessed.
 */

/** Group and decimal separators actually used by a locale. */
export interface Separators {
  readonly group: string;
  readonly decimal: string;
}

export function separatorsFor(locale: string): Separators {
  // 1234.5 formats with both separators visible in every locale that has them.
  const parts = new Intl.NumberFormat(locale).formatToParts(1234.5);
  const group = parts.find((p) => p.type === 'group')?.value ?? ',';
  const decimal = parts.find((p) => p.type === 'decimal')?.value ?? '.';
  return { group, decimal };
}

export type ParseResult =
  | { readonly ok: true; readonly value: number }
  | { readonly ok: false; readonly reason: 'empty' | 'not_a_number' | 'ambiguous' };

/**
 * Parse a number as typed in `locale`.
 *
 * Returns a result rather than `NaN`. `NaN` propagates silently through
 * arithmetic and surfaces far from its cause; a discriminated result forces the
 * caller to handle the failure where it happened.
 */
export function parseLocaleNumber(input: string, locale: string): ParseResult {
  const text = input.trim();
  if (text === '') return { ok: false, reason: 'empty' };

  const { group, decimal } = separatorsFor(locale);

  // A string containing the OTHER locale's decimal separator in a position that
  // could be either is ambiguous. "1,234" is 1234 in en-US and 1.234 in de-DE —
  // guessing gives a wrong answer 50% of the time, so refuse.
  const groupCount = text.split(group).length - 1;
  const decimalCount = text.split(decimal).length - 1;
  if (decimalCount > 1) return { ok: false, reason: 'not_a_number' };

  if (groupCount > 0 && decimalCount === 0) {
    // Groups with no decimal: valid only if every group is exactly 3 digits.
    // "1,234" passes as 1234; "1,23" does not, because it is far more likely to
    // be someone typing a decimal with the wrong separator.
    const [head, ...rest] = text.replace(/^[+-]/, '').split(group);
    const wellFormed =
      head !== undefined &&
      head.length >= 1 &&
      head.length <= 3 &&
      rest.every((chunk) => /^\d{3}$/.test(chunk));
    if (!wellFormed) return { ok: false, reason: 'ambiguous' };
  }

  const normalised = text
    .split(group)
    .join('')
    .replace(decimal, '.')
    // Strip spacing characters some locales use for grouping, including the
    // narrow no-break space that fr-FR emits and that a user cannot type.
    .replace(/[\s  ]/g, '');

  if (!/^[+-]?\d*\.?\d+$/.test(normalised)) return { ok: false, reason: 'not_a_number' };

  const value = Number(normalised);
  if (!Number.isFinite(value)) return { ok: false, reason: 'not_a_number' };
  return { ok: true, value };
}

export function formatLocaleNumber(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value);
}
