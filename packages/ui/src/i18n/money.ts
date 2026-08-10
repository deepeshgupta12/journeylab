/**
 * Money — STEP-003.07 (REQ-NFR-007).
 *
 * MONEY IS AN INTEGER COUNT OF MINOR UNITS. NEVER A FLOAT.
 *   `0.1 + 0.2 === 0.30000000000000004` in IEEE 754, and currency arithmetic is
 *   mostly addition. A budget summed from thirty float line items drifts by
 *   fractions of a cent, and the drift compounds silently — the total simply
 *   stops matching the sum of what is displayed, and nobody can say why.
 *
 *   So the representation is `{ amountMinor: 1234, currency: 'EUR' }`, meaning
 *   €12.34. Arithmetic is integer arithmetic; only formatting divides.
 *
 * MINOR UNITS ARE NOT ALWAYS 2
 *   JPY and KRW have none (¥100 is 100, not 1.00). BHD, KWD and TND have three.
 *   Hard-coding `/ 100` is wrong for currencies a travel product will certainly
 *   meet — and wrong in the direction of showing a Japanese price 100× too small.
 */

/** Exponents that are not 2. Everything absent from this map uses 2. */
const MINOR_UNIT_EXPONENT: Readonly<Record<string, number>> = {
  BIF: 0,
  CLP: 0,
  DJF: 0,
  GNF: 0,
  ISK: 0,
  JPY: 0,
  KMF: 0,
  KRW: 0,
  PYG: 0,
  RWF: 0,
  UGX: 0,
  UYI: 0,
  VND: 0,
  VUV: 0,
  XAF: 0,
  XOF: 0,
  XPF: 0,
  BHD: 3,
  IQD: 3,
  JOD: 3,
  KWD: 3,
  LYD: 3,
  OMR: 3,
  TND: 3,
};

export interface Money {
  /** Integer count of minor units. €12.34 is 1234. */
  readonly amountMinor: number;
  /** ISO 4217, uppercase. */
  readonly currency: string;
}

export class MoneyError extends Error {}

export function minorUnitExponent(currency: string): number {
  return MINOR_UNIT_EXPONENT[currency.toUpperCase()] ?? 2;
}

/**
 * Beyond this, integers are no longer exactly representable and `+` starts
 * losing cents without saying so: `2**53 + 1 === 2**53` is true in JavaScript.
 *
 * 9,007,199,254,740,991 minor units is about ninety trillion euros, so no real
 * trip reaches it — but a corrupt feed, a unit mix-up, or a currency with three
 * minor digits multiplied through a bad conversion can, and the failure would be
 * a total that is quietly wrong rather than an error anyone sees.
 */
const MAX_SAFE_MINOR = Number.MAX_SAFE_INTEGER;

export function money(amountMinor: number, currency: string): Money {
  if (!Number.isSafeInteger(amountMinor) && Number.isInteger(amountMinor)) {
    throw new MoneyError(
      `amountMinor ${amountMinor} exceeds the exactly-representable range ` +
        `(±${MAX_SAFE_MINOR}); addition would silently lose minor units`,
    );
  }
  if (!Number.isInteger(amountMinor)) {
    // Rejecting rather than rounding. A caller passing 12.34 meant €12.34 and is
    // about to record 12 minor units — 12 cents. Silently rounding would turn a
    // type error into a pricing error, which is far harder to notice.
    throw new MoneyError(
      `amountMinor must be an integer count of minor units, got ${amountMinor}. ` +
        'For 12.34 EUR pass 1234, not 12.34.',
    );
  }
  if (!/^[A-Za-z]{3}$/.test(currency)) {
    throw new MoneyError(`currency must be a 3-letter ISO 4217 code, got "${currency}"`);
  }
  return { amountMinor, currency: currency.toUpperCase() };
}

/**
 * Add. Both operands must share a currency.
 *
 * Mixing currencies is refused rather than converted: a conversion needs a rate
 * and a rate needs a timestamp, neither of which an addition operator has. An
 * implicit 1:1 would be the worst possible default.
 */
export function addMoney(a: Money, b: Money): Money {
  if (a.currency !== b.currency) {
    throw new MoneyError(`cannot add ${a.currency} to ${b.currency} without an exchange rate`);
  }
  return { amountMinor: a.amountMinor + b.amountMinor, currency: a.currency };
}

export function sumMoney(amounts: readonly Money[], currency: string): Money {
  // The currency is required even for an empty list: a zero with no currency
  // cannot be formatted, and defaulting to one would be a guess.
  return amounts.reduce((total, next) => addMoney(total, next), money(0, currency));
}

/** Format for display. This is the ONLY place a division by the exponent happens. */
export function formatMoney(value: Money, locale: string): string {
  const exponent = minorUnitExponent(value.currency);
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: value.currency,
    minimumFractionDigits: exponent,
    maximumFractionDigits: exponent,
  }).format(value.amountMinor / 10 ** exponent);
}

/**
 * Parse a major-unit decimal string into minor units.
 *
 * Uses string manipulation rather than `Math.round(parseFloat(x) * 10 ** n)`.
 *
 * AN EARLIER VERSION OF THIS COMMENT WAS WRONG, and the correction is worth
 * keeping. It claimed the float route mis-parses `1.005` as 100 minor units.
 * `Math.round(1.005 * 100)` is indeed 100 — but `1.005` has three decimals, so
 * for EUR it is REJECTED by the precision check above and never reaches any
 * multiplication. A scan of every two-decimal value from 0.01 upward, and of
 * magnitudes past `Number.MAX_SAFE_INTEGER`, found no accepted input where the
 * two routes disagree. Mutating this function to the float route does not fail
 * the suite, and that mutant is recorded as EQUIVALENT rather than papered over
 * with a test that would have to be contrived to fail.
 *
 * The string route is still the right one: it is exact by construction rather
 * than exact by empirical accident, and it does not have to be re-verified when
 * someone widens the accepted precision.
 */
export function parseMoney(major: string, currency: string): Money {
  const exponent = minorUnitExponent(currency);
  const text = major.trim();
  if (!/^-?\d+(\.\d+)?$/.test(text)) {
    throw new MoneyError(`not a decimal amount: ${text}`);
  }
  const negative = text.startsWith('-');
  const [whole = '0', fraction = ''] = text.replace('-', '').split('.');
  if (fraction.length > exponent) {
    throw new MoneyError(
      `${currency} has ${exponent} minor digits; "${text}" has ${fraction.length} and would lose precision`,
    );
  }
  const padded = fraction.padEnd(exponent, '0');
  const amount = Number(`${whole}${padded}`);
  return money(negative ? -amount : amount, currency);
}
