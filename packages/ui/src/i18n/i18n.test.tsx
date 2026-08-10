/**
 * Locale, time zone, currency and DST — TST-NFR-007, TST-NFR-008 · STEP-003.07.
 *
 * The DST assertions are the ones that matter. The sub-step record says why:
 * "DST correctness is a feasibility concern, not formatting: an itinerary
 * crossing a transition computes wrong travel windows, which STEP-012 will then
 * present as a valid plan."
 *
 * A formatting bug shows a wrong string. A DST bug ships a wrong plan.
 */

import { cleanup, render, screen } from '@testing-library/react';
import axe from 'axe-core';
import { afterEach, describe, expect, it } from 'vitest';

import {
  crossesDstTransition,
  elapsedHours,
  formatDateTime,
  formatNumber,
  formatRelative,
  hoursInDay,
  zonedTimeToUtc,
} from './datetime';
import {
  createTranslator,
  FALLBACK_LOCALE,
  interpolate,
  type MessageCatalogue,
  resolveLocale,
} from './messages';
import {
  addMoney,
  formatMoney,
  MoneyError,
  minorUnitExponent,
  money,
  parseMoney,
  sumMoney,
} from './money';

afterEach(cleanup);

/** Unicode spaces Intl emits as group and NBSP separators, normalised for comparison. */
function normalise(text: string): string {
  return text.replace(/[   ]/g, ' ');
}

// --- TST-NFR-007: the locale matrix ------------------------------------------

describe('locale matrix', () => {
  // One instant, rendered for each locale in the support matrix. The point is
  // that the SAME moment is described differently, not that a string is pretty:
  // 03/04 is 3 April in the UK and 4 March in the US, and a traveller reading
  // the wrong one misses a flight.
  const instant = new Date('2026-04-03T14:30:00Z');

  it('renders one instant differently per locale and identically per zone', () => {
    const inLondon = { timeZone: 'Europe/London' };
    expect(formatDateTime(instant, { locale: 'en-GB', ...inLondon })).toMatch(/3 Apr 2026/);
    expect(formatDateTime(instant, { locale: 'en-US', ...inLondon })).toMatch(/Apr 3, 2026/);
    expect(formatDateTime(instant, { locale: 'de-DE', ...inLondon })).toMatch(/03\.04\.2026/);
    expect(formatDateTime(instant, { locale: 'ja-JP', ...inLondon })).toMatch(/2026\/04\/03/);
  });

  it('renders the same instant as a DIFFERENT DAY in a different zone', () => {
    // 14:30 UTC on 3 April is 23:30 in Tokyo — same day — but 01:30 on the 4th in
    // Auckland. A formatter that ignores the zone silently loses a day here.
    const auckland = formatDateTime(instant, { locale: 'en-GB', timeZone: 'Pacific/Auckland' });
    expect(auckland).toMatch(/4 Apr 2026/);
    const honolulu = formatDateTime(instant, { locale: 'en-GB', timeZone: 'Pacific/Honolulu' });
    expect(honolulu).toMatch(/3 Apr 2026/);
  });

  it('formats numbers per locale, including the separators that swap meaning', () => {
    // "1.234" is one thousand two hundred and thirty-four in German and one point
    // two three four in English. This is the classic budget-off-by-1000 bug.
    expect(normalise(formatNumber(1234.5, 'en-GB'))).toBe('1,234.5');
    expect(normalise(formatNumber(1234.5, 'de-DE'))).toBe('1.234,5');
    expect(normalise(formatNumber(1234.5, 'fr-FR'))).toBe('1 234,5');
  });

  it('formats relative durations with the target language grammar', () => {
    expect(formatRelative(3, 'en-GB')).toBe('in 3 hours');
    expect(formatRelative(-3, 'en-GB')).toBe('3 hours ago');
    expect(formatRelative(48, 'en-GB')).toBe('in 2 days');
    // Not a hand-built "in N days" template. German inflects the noun — "in 3
    // Tagen", not "in 3 Tage" — and at two days out it does not use a number at
    // all. A template that produced "in 2 Tage" would be wrong twice over.
    expect(formatRelative(72, 'de-DE')).toBe('in 3 Tagen');
    expect(formatRelative(48, 'de-DE')).toBe('\u00fcbermorgen');
  });

  it('REFUSES an absent zone at runtime, not only at compile time', () => {
    // TypeScript makes timeZone required and that is worthless at the package
    // boundary: JS consumers, `any` from a fetch, and optional fields two layers
    // up all arrive as undefined. Intl treats `timeZone: undefined` as "use the
    // system zone" — so without this check the failure is not an exception, it is
    // a server silently rendering in the container's zone.
    // @ts-expect-error timeZone is not optional
    expect(() => formatDateTime(instant, { locale: 'en-GB' })).toThrow(TypeError);
    expect(() => formatDateTime(instant, { locale: 'en-GB', timeZone: '' })).toThrow(TypeError);
  });

  it('refuses a misspelled zone rather than falling back to the system one', () => {
    expect(() => formatDateTime(instant, { locale: 'en-GB', timeZone: 'Europe/Londn' })).toThrow(
      /unknown IANA time zone/,
    );
    expect(() => zonedTimeToUtc({ year: 2026, month: 1, day: 1 }, 'Mars/Olympus')).toThrow(
      /unknown IANA time zone/,
    );
  });
});

// --- the DST assertions -------------------------------------------------------

describe('DST transitions', () => {
  // Europe/London springs forward 2026-03-29 (01:00 -> 02:00) and falls back
  // 2026-10-25 (02:00 -> 01:00). Verified against the IANA rule, not guessed.

  it('a spring-forward day is 23 hours long, not 24', () => {
    expect(hoursInDay({ year: 2026, month: 3, day: 29 }, 'Europe/London')).toBe(23);
  });

  it('a fall-back day is 25 hours long', () => {
    expect(hoursInDay({ year: 2026, month: 10, day: 25 }, 'Europe/London')).toBe(25);
  });

  it('an ordinary day is 24 hours', () => {
    expect(hoursInDay({ year: 2026, month: 6, day: 15 }, 'Europe/London')).toBe(24);
    expect(crossesDstTransition({ year: 2026, month: 6, day: 15 }, 'Europe/London')).toBe(false);
    expect(crossesDstTransition({ year: 2026, month: 3, day: 29 }, 'Europe/London')).toBe(true);
  });

  it('A DATE RANGE SPANNING A TRANSITION COMPUTES THE CORRECT DURATION', () => {
    // The §7 test the sub-step names. 22:00 the night before to 06:00 the morning
    // after the spring-forward is EIGHT wall-clock hours and SEVEN real ones.
    const departure = zonedTimeToUtc(
      { year: 2026, month: 3, day: 28, hour: 22, minute: 0 },
      'Europe/London',
    );
    const arrival = zonedTimeToUtc(
      { year: 2026, month: 3, day: 29, hour: 6, minute: 0 },
      'Europe/London',
    );
    expect(elapsedHours(departure, arrival)).toBe(7);

    // Wall-clock subtraction — what naive arithmetic does — says 8. That one hour
    // is the entire defect: a 90-minute connection becomes 30.
    const naive = 6 + 24 - 22;
    expect(naive).toBe(8);
  });

  it('computes the correct duration across a fall-back too', () => {
    const from = zonedTimeToUtc(
      { year: 2026, month: 10, day: 24, hour: 23, minute: 0 },
      'Europe/London',
    );
    const to = zonedTimeToUtc(
      { year: 2026, month: 10, day: 25, hour: 5, minute: 0 },
      'Europe/London',
    );
    // Six wall-clock hours, seven real ones — the extra hour is the repeated 01:00.
    expect(elapsedHours(from, to)).toBe(7);
  });

  it('handles a zone with a half-hour offset and no DST', () => {
    // Asia/Kolkata is UTC+5:30 year round. A codebase that stores offsets as whole
    // hours is wrong for a fifth of the world's population.
    const instant = zonedTimeToUtc(
      { year: 2026, month: 6, day: 1, hour: 9, minute: 0 },
      'Asia/Kolkata',
    );
    expect(instant.toISOString()).toBe('2026-06-01T03:30:00.000Z');
    expect(hoursInDay({ year: 2026, month: 6, day: 1 }, 'Asia/Kolkata')).toBe(24);
  });

  it('handles the southern hemisphere, where the transitions are reversed', () => {
    // Australia/Sydney springs forward in OCTOBER. A test suite that only checks
    // Europe encodes a northern-hemisphere assumption it never states.
    expect(hoursInDay({ year: 2026, month: 10, day: 4 }, 'Australia/Sydney')).toBe(23);
    expect(hoursInDay({ year: 2026, month: 4, day: 5 }, 'Australia/Sydney')).toBe(25);
  });

  it('round-trips a wall-clock time that is not midnight', () => {
    const instant = zonedTimeToUtc(
      { year: 2026, month: 7, day: 14, hour: 8, minute: 30 },
      'Europe/London',
    );
    // 08:30 BST is 07:30 UTC.
    expect(instant.toISOString()).toBe('2026-07-14T07:30:00.000Z');
  });

  it('resolves a wall-clock time that does not exist without crashing', () => {
    // 01:30 on 2026-03-29 in London never happens — the clock jumps 01:00 -> 02:00.
    // The requirement is that this is DETERMINISTIC and forward-shifted, not that
    // it is "correct": there is no correct answer, so the contract is the answer.
    const instant = zonedTimeToUtc(
      { year: 2026, month: 3, day: 29, hour: 1, minute: 30 },
      'Europe/London',
    );
    expect(instant.toISOString()).toBe('2026-03-29T01:30:00.000Z'); // 02:30 BST
    expect(
      zonedTimeToUtc(
        { year: 2026, month: 3, day: 29, hour: 1, minute: 30 },
        'Europe/London',
      ).getTime(),
    ).toBe(instant.getTime());
  });
});

// --- money --------------------------------------------------------------------

describe('money as integer minor units', () => {
  it('rejects a float amount rather than rounding it', () => {
    // Rounding would turn a type error into a pricing error: 12.34 passed as
    // minor units is 12 cents, and nothing would say so.
    expect(() => money(12.34, 'EUR')).toThrow(MoneyError);
    expect(() => money(1234, 'EUR')).not.toThrow();
  });

  it('does NOT accumulate float error across a long sum', () => {
    // The reason the whole module exists. Thirty ten-cent items.
    const items = Array.from({ length: 30 }, () => money(10, 'EUR'));
    expect(sumMoney(items, 'EUR').amountMinor).toBe(300);

    // The same sum in floats does not equal 3.00.
    let float = 0;
    for (let i = 0; i < 30; i += 1) float += 0.1;
    expect(float).not.toBe(3);
  });

  it('refuses to add across currencies instead of assuming 1:1', () => {
    expect(() => addMoney(money(100, 'EUR'), money(100, 'USD'))).toThrow(/exchange rate/);
  });

  it('knows the minor-unit exponent is not always 2', () => {
    expect(minorUnitExponent('EUR')).toBe(2);
    expect(minorUnitExponent('JPY')).toBe(0);
    expect(minorUnitExponent('KWD')).toBe(3);
    expect(minorUnitExponent('jpy')).toBe(0); // case-insensitive
  });

  it('formats a zero-exponent currency without inventing decimals', () => {
    // 100 JPY minor units is ¥100, not ¥1.00. Hard-coding /100 shows a Japanese
    // price one hundred times too small.
    expect(normalise(formatMoney(money(100, 'JPY'), 'ja-JP'))).toBe('￥100');
    expect(normalise(formatMoney(money(1234, 'EUR'), 'en-GB'))).toBe('€12.34');
    expect(normalise(formatMoney(money(1234, 'EUR'), 'de-DE'))).toBe('12,34 €');
    // Three-decimal currency.
    expect(normalise(formatMoney(money(1234, 'KWD'), 'en-GB'))).toMatch(/1\.234/);
  });

  it('parses a decimal string exactly, where float multiplication does not', () => {
    // Math.round(1.005 * 100) is 100, because 1.005 is stored as 1.00499999...
    expect(Math.round(1.005 * 100)).toBe(100);
    expect(parseMoney('1.005', 'KWD').amountMinor).toBe(1005);
    expect(parseMoney('12.34', 'EUR').amountMinor).toBe(1234);
    expect(parseMoney('12.3', 'EUR').amountMinor).toBe(1230);
    expect(parseMoney('12', 'EUR').amountMinor).toBe(1200);
    expect(parseMoney('-12.34', 'EUR').amountMinor).toBe(-1234);
    expect(parseMoney('100', 'JPY').amountMinor).toBe(100);
  });

  it('refuses precision it cannot represent rather than truncating', () => {
    expect(() => parseMoney('12.345', 'EUR')).toThrow(/lose precision/);
    expect(() => parseMoney('12.5', 'JPY')).toThrow(/lose precision/);
    expect(() => parseMoney('twelve', 'EUR')).toThrow(MoneyError);
  });

  it('refuses an amount too large to add without silently losing cents', () => {
    // 2**53 + 1 === 2**53 in JavaScript, so past MAX_SAFE_INTEGER addition stops
    // being exact and says nothing about it.
    expect(() => money(Number.MAX_SAFE_INTEGER, 'EUR')).not.toThrow();
    expect(() => money(Number.MAX_SAFE_INTEGER + 2, 'EUR')).toThrow(/exactly-representable/);
    expect(() => money(-(Number.MAX_SAFE_INTEGER + 2), 'EUR')).toThrow(/exactly-representable/);
  });

  it('requires a currency even for an empty sum', () => {
    // A zero with no currency cannot be formatted, and picking one is a guess.
    expect(sumMoney([], 'EUR')).toEqual({ amountMinor: 0, currency: 'EUR' });
  });
});

// --- messages and fallback ------------------------------------------------------

describe('message catalogue', () => {
  const en: MessageCatalogue = { 'a.b': 'Hello {name}', only: 'English only' };
  const fr: MessageCatalogue = { 'a.b': 'Bonjour {name}' };

  it('resolves from the catalogue and interpolates', () => {
    expect(createTranslator('fr', fr, en).t('a.b', { name: 'Ada' })).toBe('Bonjour Ada');
  });

  it('FALLS BACK WITHOUT CRASHING when the locale lacks a key', () => {
    // §12: "Missing locale falls back without crashing."
    expect(createTranslator('fr', fr, en).t('only')).toBe('English only');
  });

  it('returns the KEY for a message no catalogue has', () => {
    // Not an empty string. Blank text looks like a layout bug and is triaged as
    // one; a visible `trip.brief.title` reaches the right person.
    expect(createTranslator('fr', fr, en).t('nowhere.at.all')).toBe('nowhere.at.all');
  });

  it('leaves an unresolved placeholder visible', () => {
    expect(interpolate('Hello {name}')).toBe('Hello {name}');
    expect(interpolate('{a} and {b}', { a: '1' })).toBe('1 and {b}');
  });

  it('interpolates numbers as well as strings', () => {
    expect(interpolate('{n} nights', { n: 3 })).toBe('3 nights');
  });

  it('reports whether a key came from the real catalogue', () => {
    const t = createTranslator('fr', fr, en);
    expect(t.has('a.b')).toBe(true);
    expect(t.has('only')).toBe(false); // present, but only via fallback
  });

  it('resolves a regional tag to its base language before the default', () => {
    // The fallback is deliberately a DIFFERENT language from the expected answer.
    // A first version of this used ['fr', 'en'] with the default fallback, so
    // deleting the base-language branch entirely still returned 'en' — the test
    // passed for the wrong reason and a mutation proved it.
    expect(resolveLocale('en-AU', ['fr', 'en-GB'], 'fr')).toBe('en-GB');
    expect(resolveLocale('de-CH', ['de', 'en'], 'en')).toBe('de');
    expect(resolveLocale('zz', ['fr', 'en'])).toBe(FALLBACK_LOCALE);
  });

  it('prefers an exact match over a base-language one, case-insensitively', () => {
    // Both entries share the primary subtag, so a case-sensitive exact check
    // would fall through to the base match and return the wrong one.
    expect(resolveLocale('en-GB', ['en', 'en-GB'])).toBe('en-GB');
    expect(resolveLocale('EN-gb', ['en', 'en-GB'])).toBe('en-GB');
    expect(resolveLocale('en', ['en', 'en-GB'])).toBe('en');
  });

  it('is a pure function of its arguments — no module-level current locale', () => {
    // A cached "current locale" on a server handling concurrent requests is
    // shared mutable state; the failure mode is one user seeing another's
    // language. Two translators must coexist without interfering.
    const a = createTranslator('en', en);
    const b = createTranslator('fr', fr, en);
    expect(a.t('a.b', { name: 'X' })).toBe('Hello X');
    expect(b.t('a.b', { name: 'X' })).toBe('Bonjour X');
    expect(a.t('a.b', { name: 'X' })).toBe('Hello X');
  });
});

// --- TST-NFR-008: RTL structure -------------------------------------------------

async function axeViolations(container: HTMLElement) {
  const results = await axe.run(container, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
  });
  return results.violations.map((v) => `${v.id}: ${v.help}`);
}

describe('RTL structure', () => {
  function Card({ title, amount }: { title: string; amount: string }) {
    return (
      <section aria-label={title}>
        <h2>{title}</h2>
        <p>{amount}</p>
      </section>
    );
  }

  it('renders content unchanged under dir="rtl"', () => {
    // Structure, not appearance: the sub-step scopes RTL *implementation* to
    // Phase 2. What must hold now is that direction is a container concern and
    // no component hard-codes a side.
    const { container } = render(
      <div dir="rtl" lang="ar">
        <Card title="رحلة" amount="١٢٫٣٤ €" />
      </div>,
    );
    expect(screen.getByRole('heading', { name: 'رحلة' })).toBeDefined();
    expect(container.querySelector('[dir="rtl"]')).not.toBeNull();
  });

  it('passes axe under an RTL locale', async () => {
    const { container } = render(
      <div dir="rtl" lang="ar">
        <Card title="رحلة" amount="١٢٫٣٤ €" />
      </div>,
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it('formats an RTL locale without throwing', () => {
    const instant = new Date('2026-04-03T14:30:00Z');
    expect(formatDateTime(instant, { locale: 'ar-EG', timeZone: 'Africa/Cairo' })).toBeTruthy();
    expect(formatMoney(money(1234, 'EGP'), 'ar-EG')).toBeTruthy();
  });
});
