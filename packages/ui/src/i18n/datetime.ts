/**
 * Locale and time-zone formatting — STEP-003.07 (REQ-NFR-007).
 *
 * DST IS A FEASIBILITY CONCERN, NOT A FORMATTING ONE
 *   The sub-step record says it exactly: "an itinerary crossing a transition
 *   computes wrong travel windows, which STEP-012 will then present as a valid
 *   plan."
 *
 *   The night of 29 March 2026 in Europe/London is 23 hours long. A connection
 *   with a 90-minute buffer that straddles 01:00 has 30 minutes. Arithmetic that
 *   assumes 24-hour days produces a plan that is wrong and looks fine — which is
 *   worse than one that fails, because the solver will have declared it feasible.
 *
 * FORMATTING RUNS SERVER-SIDE WITH AN EXPLICIT LOCALE AND ZONE
 *   §4 asked this to be decided and documented. The decision:
 *
 *   Every formatter here takes `locale` and `timeZone` as REQUIRED arguments.
 *   None reads the ambient environment. That is what makes server and client
 *   produce identical output — the usual hydration mismatch is a server
 *   rendering in UTC and a browser re-rendering in its own zone, which React
 *   reports as a mismatch and a user sees as a flicker to a different time.
 *
 *   The zone comes from the TRIP, not the reader. A traveller checking their
 *   Tokyo itinerary from London wants Tokyo times; the browser's zone would show
 *   them something true and useless.
 */

import { isValidTimeZone } from '../form/zoned-date';

export const MILLIS_PER_HOUR = 3_600_000;

export interface FormatOptions {
  readonly locale: string;
  /** IANA zone. Required — see the module note on hydration. */
  readonly timeZone: string;
}

/**
 * Reject an absent or unknown zone at RUNTIME, not only at compile time.
 *
 * TypeScript makes `timeZone` required, and that is worthless at the package
 * boundary: a JavaScript consumer, an `any` from a fetch response, or a field
 * that is optional two layers up all reach here as `undefined`. And
 * `Intl.DateTimeFormat` treats `timeZone: undefined` as "use the system zone" —
 * so the failure is not an exception, it is a server rendering in whatever zone
 * the container happens to have. Silent, environment-dependent, and exactly the
 * hydration mismatch this module exists to prevent.
 *
 * An unknown zone string is refused for the same reason: `Intl` throws for some
 * inputs and normalises others, and "Europe/Londn" must never quietly become the
 * system default.
 */
function assertZone(timeZone: string): string {
  if (typeof timeZone !== 'string' || timeZone.trim() === '') {
    throw new TypeError(
      "timeZone is required. Pass the trip's IANA zone explicitly — omitting it " +
        'makes Intl use the system zone, which differs between server and browser.',
    );
  }
  if (!isValidTimeZone(timeZone)) {
    throw new RangeError(`unknown IANA time zone: ${timeZone}`);
  }
  return timeZone;
}

export function formatDateTime(
  instant: Date,
  { locale, timeZone }: FormatOptions,
  style: Intl.DateTimeFormatOptions = { dateStyle: 'medium', timeStyle: 'short' },
): string {
  return new Intl.DateTimeFormat(locale, { ...style, timeZone: assertZone(timeZone) }).format(
    instant,
  );
}

export function formatDate(instant: Date, options: FormatOptions): string {
  return formatDateTime(instant, options, { dateStyle: 'medium' });
}

export function formatTime(instant: Date, options: FormatOptions): string {
  return formatDateTime(instant, options, { timeStyle: 'short' });
}

/**
 * Elapsed hours between two instants.
 *
 * This is REAL elapsed time and is DST-correct for free, because both operands
 * are instants and subtraction of instants cannot be fooled by a wall clock that
 * jumped. The trap is upstream: constructing those instants from wall-clock
 * dates without a zone.
 */
export function elapsedHours(from: Date, to: Date): number {
  return (to.getTime() - from.getTime()) / MILLIS_PER_HOUR;
}

interface ZonedParts {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
}

function partsIn(instant: Date, timeZone: string): ZonedParts {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: assertZone(timeZone),
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(instant);
  const get = (type: string): number => Number(parts.find((p) => p.type === type)?.value ?? '0');
  return {
    year: get('year'),
    month: get('month'),
    day: get('day'),
    hour: get('hour') % 24,
    minute: get('minute'),
  };
}

/**
 * The instant at a given wall-clock time in a zone.
 *
 * Two-pass, because a single offset correction can itself cross a transition.
 * This is the same approach as `form/zoned-date.ts`, which handles midnight; this
 * generalises it to any wall time so a departure at 08:30 local is as safe as a
 * date boundary.
 */
export function zonedTimeToUtc(
  wall: { year: number; month: number; day: number; hour?: number; minute?: number },
  timeZone: string,
): Date {
  const naive = Date.UTC(wall.year, wall.month - 1, wall.day, wall.hour ?? 0, wall.minute ?? 0);
  const shown = partsIn(new Date(naive), timeZone);
  const shownUtc = Date.UTC(shown.year, shown.month - 1, shown.day, shown.hour, shown.minute);
  const first = new Date(naive - (shownUtc - naive));

  const check = partsIn(first, timeZone);
  if (check.hour === (wall.hour ?? 0) && check.minute === (wall.minute ?? 0)) return first;

  const checkUtc = Date.UTC(check.year, check.month - 1, check.day, check.hour, check.minute);
  return new Date(first.getTime() - (checkUtc - naive));
}

/**
 * Hours in a calendar day in a given zone. **Not always 24.**
 *
 * 23 on a spring-forward day, 25 on a fall-back day. Any duration arithmetic that
 * multiplies days by 24 is wrong twice a year in most of the world, and the error
 * is exactly the size of a missed connection.
 */
export function hoursInDay(
  date: { year: number; month: number; day: number },
  timeZone: string,
): number {
  const start = zonedTimeToUtc({ ...date, hour: 0, minute: 0 }, timeZone);
  const nextDay = new Date(Date.UTC(date.year, date.month - 1, date.day + 1));
  const next = zonedTimeToUtc(
    {
      year: nextDay.getUTCFullYear(),
      month: nextDay.getUTCMonth() + 1,
      day: nextDay.getUTCDate(),
      hour: 0,
      minute: 0,
    },
    timeZone,
  );
  return elapsedHours(start, next);
}

/** True when the calendar day is not 24 hours long in that zone. */
export function crossesDstTransition(
  date: { year: number; month: number; day: number },
  timeZone: string,
): boolean {
  return hoursInDay(date, timeZone) !== 24;
}

export function formatNumber(
  value: number,
  locale: string,
  options?: Intl.NumberFormatOptions,
): string {
  return new Intl.NumberFormat(locale, options).format(value);
}

/**
 * Human duration, in the reader's locale.
 *
 * `Intl.RelativeTimeFormat` handles the grammar — "in 3 days" versus "vor 3
 * Tagen" — which hand-built strings get wrong in every language with cases.
 */
export function formatRelative(deltaHours: number, locale: string): string {
  const formatter = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
  const absolute = Math.abs(deltaHours);
  if (absolute < 24) return formatter.format(Math.round(deltaHours), 'hour');
  return formatter.format(Math.round(deltaHours / 24), 'day');
}
