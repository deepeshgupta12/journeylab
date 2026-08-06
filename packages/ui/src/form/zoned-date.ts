/**
 * Time-zone-explicit date entry — STEP-003.02.
 *
 * THE FAILURE THIS EXISTS TO PREVENT
 *   The sub-step record names it: "Date inputs are where time-zone bugs enter the
 *   product; a naive local date here becomes an infeasible itinerary in STEP-012."
 *
 *   `new Date("2026-08-06")` is parsed as UTC midnight. `new Date("2026-08-06T00:00")`
 *   is parsed in the BROWSER's zone. The same trip start date therefore means two
 *   different instants depending on which string form a component happened to
 *   build — and for a traveller in Auckland, UTC midnight is already the following
 *   afternoon.
 *
 *   So there is no function here that turns a date string into an instant without
 *   an IANA time zone. The zone is a required argument, not an option with a
 *   default, because a default would be a guess about where the user is.
 *
 * This mirrors the Python side, where ruff's DTZ rules ban naive datetimes for the
 * same reason (see pyproject.toml).
 */

/** A calendar date with no instant attached. This is what a date input holds. */
export interface CalendarDate {
  readonly year: number;
  readonly month: number; // 1-12, not the 0-11 that Date uses
  readonly day: number;
}

export type DateParseResult =
  | { readonly ok: true; readonly date: CalendarDate }
  | { readonly ok: false; readonly reason: 'empty' | 'malformed' | 'impossible' };

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Parse the `YYYY-MM-DD` value an `<input type="date">` produces.
 *
 * Deliberately returns a `CalendarDate`, never a `Date`. A `Date` is an instant,
 * and the value of a date input is not one — conflating them is the bug.
 */
export function parseCalendarDate(value: string): DateParseResult {
  const text = value.trim();
  if (text === '') return { ok: false, reason: 'empty' };

  const match = ISO_DATE.exec(text);
  if (!match) return { ok: false, reason: 'malformed' };

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);

  // Round-trip through UTC to reject 2026-02-30, which `Date` would silently
  // roll forward to 2 March rather than refusing.
  const probe = new Date(Date.UTC(year, month - 1, day));
  if (
    probe.getUTCFullYear() !== year ||
    probe.getUTCMonth() !== month - 1 ||
    probe.getUTCDate() !== day
  ) {
    return { ok: false, reason: 'impossible' };
  }
  return { ok: true, date: { year, month, day } };
}

/**
 * The UTC instant at which `date` begins in `timeZone`.
 *
 * `timeZone` is required. There is no overload that omits it.
 *
 * Implemented by probing the offset rather than assuming one, because offsets
 * change with DST: 2026-03-29 in Europe/London begins at 00:00 GMT, while
 * 2026-06-01 begins at 23:00 UTC the previous day.
 */
export function startOfDayUtc(date: CalendarDate, timeZone: string): Date {
  const naiveUtc = Date.UTC(date.year, date.month - 1, date.day, 0, 0, 0);
  // What wall-clock time does that instant show in the target zone?
  const shown = zonedParts(new Date(naiveUtc), timeZone);
  const shownAsUtc = Date.UTC(
    shown.year,
    shown.month - 1,
    shown.day,
    shown.hour,
    shown.minute,
    shown.second,
  );
  // The difference is the zone offset at that moment; subtract it to land on
  // local midnight. A second pass handles the case where the first correction
  // crosses a DST boundary.
  const firstPass = new Date(naiveUtc - (shownAsUtc - naiveUtc));
  const check = zonedParts(firstPass, timeZone);
  if (check.hour === 0 && check.minute === 0) return firstPass;

  const checkAsUtc = Date.UTC(
    check.year,
    check.month - 1,
    check.day,
    check.hour,
    check.minute,
    check.second,
  );
  return new Date(firstPass.getTime() - (checkAsUtc - naiveUtc));
}

interface ZonedParts {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  second: number;
}

function zonedParts(instant: Date, timeZone: string): ZonedParts {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(instant);

  const get = (type: string): number => Number(parts.find((p) => p.type === type)?.value ?? '0');
  // hourCycle can render midnight as 24; normalise so arithmetic stays sane.
  const hour = get('hour') % 24;
  return {
    year: get('year'),
    month: get('month'),
    day: get('day'),
    hour,
    minute: get('minute'),
    second: get('second'),
  };
}

/** True when the IANA zone is one this runtime recognises. */
export function isValidTimeZone(timeZone: string): boolean {
  try {
    new Intl.DateTimeFormat('en', { timeZone });
    return true;
  } catch {
    return false;
  }
}
