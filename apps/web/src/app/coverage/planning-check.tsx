'use client';

import { DateInput, Notification, NotificationRegion, Select } from '@journeylab/ui';
import { useState } from 'react';
import type { CoverageRegion } from './fetch-coverage';

/**
 * "Can you plan this?" — STEP-007.03 (REQ-TRIP-001, REQ-TRIP-002, REQ-A11Y-001).
 *
 * THE ANSWER IS NOT COMPUTED HERE, AND THAT IS THE POINT
 *   Every bound this form could check is already in the coverage document sitting
 *   in the page above it, so validating locally would be easy and would be the
 *   second implementation of a rule `POST /trips` must also enforce. `BUG-029` is
 *   what that costs — a projection and a contract disagreeing about the same field
 *   in two languages. The server decides; this component asks and renders.
 *
 *   The one thing checked locally is *did you fill both dates in*, which is not a
 *   coverage rule. It exists so an empty form does not spend a network round trip
 *   to be told what the form already knows.
 *
 * A REFUSAL IS ANNOUNCED, NOT ONLY SHOWN
 *   `REQ-A11Y-001`. The result replaces content further down the page, which a
 *   screen-reader user has no reason to be looking at. It is rendered inside a live
 *   region so the answer reaches them at the moment it arrives.
 *
 *   `assertive` for a refusal, `polite` for an acceptance. The distinction is not
 *   decorative: a refusal means the thing they just asked for cannot happen and
 *   every subsequent keystroke is wasted, which is what `role="alert"` is for. An
 *   acceptance can wait for a pause in speech.
 *
 * NO PARTIAL RESULT IS RENDERED ON A REFUSAL
 *   `REQ-TRIP-002`. There is no branch here that shows a trip outline, a suggested
 *   itinerary or a greyed-out plan. A refused request produces a sentence and the
 *   supported bounds, and nothing that looks like an answer.
 */

/** Mirrors `PlanningAccepted` in the contract. */
interface Accepted {
  readonly region_id: string;
  readonly display_name: string;
  readonly nights: number;
  readonly disclosures: readonly string[];
}

/** The subset of RFC 9457 this component renders. */
interface Refusal {
  readonly code: string;
  readonly detail?: string;
  readonly retryable: boolean;
  readonly remediation?: Record<string, unknown>;
}

type Outcome =
  | { readonly kind: 'idle' }
  | { readonly kind: 'asking' }
  | { readonly kind: 'accepted'; readonly accepted: Accepted }
  | { readonly kind: 'refused'; readonly refusal: Refusal }
  | { readonly kind: 'unreachable' };

const API_BASE = process.env.NEXT_PUBLIC_JOURNEYLAB_API_URL ?? 'http://127.0.0.1:5710';

export function PlanningCheck({ regions }: { readonly regions: readonly CoverageRegion[] }) {
  const [regionId, setRegionId] = useState(regions[0]?.region_id ?? '');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [outcome, setOutcome] = useState<Outcome>({ kind: 'idle' });
  const [formError, setFormError] = useState('');

  // A region has to be declared before anything can be asked about it. Rendering a
  // form over an empty list would offer a control that cannot produce an answer,
  // which reads as broken rather than as honest.
  if (regions.length === 0) {
    return (
      <section aria-labelledby="check-unavailable">
        <h2 id="check-unavailable">Check your dates</h2>
        <p>
          There is nothing to check yet. No region has been declared, so there is no destination
          this form could ask about. It will appear here as soon as one is supported.
        </p>
      </section>
    );
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!start || !end) {
      setFormError('Enter both a start and an end date.');
      return;
    }
    setFormError('');
    setOutcome({ kind: 'asking' });
    try {
      const response = await fetch(`${API_BASE}/coverage:check`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', accept: 'application/json' },
        body: JSON.stringify({ region_id: regionId, start_date: start, end_date: end }),
      });
      const body = await response.json();
      if (response.ok) {
        setOutcome({ kind: 'accepted', accepted: body as Accepted });
      } else {
        setOutcome({ kind: 'refused', refusal: body as Refusal });
      }
    } catch {
      // The caught error carries a host and a port and this string is rendered to
      // the public, so it is not surfaced. `fetch-coverage.ts` makes the same call.
      setOutcome({ kind: 'unreachable' });
    }
  }

  return (
    <section aria-labelledby="check-heading">
      <h2 id="check-heading">Check your dates</h2>
      <p>
        Tell us where and when, and we will say whether we can plan it. Dates are checked in the
        destination&rsquo;s time zone, not yours, so the answer can differ by a day from your own
        calendar.
      </p>

      <form onSubmit={onSubmit} noValidate>
        <Select
          label="Destination"
          value={regionId}
          onChange={(e) => setRegionId(e.currentTarget.value)}
          options={regions.map((r) => ({ value: r.region_id, label: r.display_name }))}
          required
        />

        {/* `DateInput`, not a raw input. It yields a CALENDAR DATE and refuses to
            produce an instant, because converting one needs a zone and the browser's
            is the wrong one — which is the whole subject of this sub-step. It also
            already knows that `aria-required` is unsupported on `input[type=date]`,
            a lesson STEP-003.02 recorded and this file rediscovered. */}
        <DateInput label="First day" value={start} onDateChange={(raw) => setStart(raw)} required />
        <DateInput label="Last day" value={end} onDateChange={(raw) => setEnd(raw)} required />

        {formError ? <p role="alert">{formError}</p> : null}

        <button type="submit" className="jl-button" disabled={outcome.kind === 'asking'}>
          {outcome.kind === 'asking' ? 'Checking…' : 'Check these dates'}
        </button>
      </form>

      <NotificationRegion
        polite={
          outcome.kind === 'accepted' ? (
            <Notification politeness="polite" title="We can plan this">
              <p>
                {outcome.accepted.nights} night{outcome.accepted.nights === 1 ? '' : 's'} in{' '}
                {outcome.accepted.display_name}. Nothing has been created yet &mdash; this is only
                an answer about whether we can.
              </p>
              {outcome.accepted.disclosures.length > 0 ? (
                <ul>
                  {outcome.accepted.disclosures.map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              ) : null}
            </Notification>
          ) : null
        }
        assertive={
          outcome.kind === 'refused' ? (
            <Notification politeness="assertive" title="We cannot plan this">
              <p>{outcome.refusal.detail}</p>
              {outcome.refusal.remediation ? (
                <Bounds remediation={outcome.refusal.remediation} />
              ) : null}
              {outcome.refusal.retryable ? (
                <p>This is usually temporary. It is worth trying again later.</p>
              ) : null}
            </Notification>
          ) : outcome.kind === 'unreachable' ? (
            <Notification politeness="assertive" title="We could not check">
              <p>
                We could not reach the coverage service. This is a problem on our side, not a
                statement that your destination is unsupported.
              </p>
            </Notification>
          ) : null
        }
      />
    </section>
  );
}

/**
 * The supported bounds, where the refusal carries them.
 *
 * Deliberately renders only the shapes it recognises. `remediation` is an open
 * object in the contract, and rendering unknown keys generically would put whatever
 * a future server sends straight onto the page. It shows guidance, never a
 * suggested trip &mdash; the distinction `REQ-TRIP-002` rests on.
 */
function Bounds({ remediation }: { readonly remediation: Record<string, unknown> }) {
  const days = remediation.supported_trip_days as
    | { minimum?: number; maximum?: number }
    | undefined;
  const dates = remediation.supported_dates as { start?: string; end?: string } | undefined;
  const today = remediation.today_at_destination as string | undefined;

  return (
    <>
      {days?.minimum && days.maximum ? (
        <p>
          We plan trips of {days.minimum} to {days.maximum} days.
        </p>
      ) : null}
      {dates?.start && dates.end ? (
        <p>
          We can plan this region between {dates.start} and {dates.end}.
        </p>
      ) : null}
      {today ? <p>It is already {today} at the destination.</p> : null}
    </>
  );
}
