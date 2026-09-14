/**
 * @vitest-environment jsdom
 *
 * Requested per file rather than per package — see `planning-check.test.tsx`.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test } from 'vitest';
import { DegradationNotice } from './degradation';
import type { CoverageRegion } from './fetch-coverage';

/**
 * STEP-007.05 — the degraded-state banner (REQ-EVID-006, REQ-EVID-001, REQ-A11Y-001).
 *
 * WHAT ONLY A RENDERED DOCUMENT CAN ANSWER
 *   Whether the live region re-announces on a re-render. That is a property of
 *   what happened over time, not of the final DOM — the markup is identical
 *   whether the text was set once or fifty times — which is why the component
 *   publishes a count for it. An unobservable property is one nothing is checking.
 */

const OBSERVED = '2026-09-14T08:00:00+00:00';

const REGIONS: readonly CoverageRegion[] = [
  {
    region_id: 'ch-bo',
    display_name: 'Bernese Oberland',
    date_bounds: { start: '2026-01-01', end: '2026-12-31' },
    freshness: 'degraded',
    limitations: ['ch-bo is running on degraded sources'],
  },
  {
    region_id: 'ch-vs',
    display_name: 'Valais',
    date_bounds: { start: '2026-01-01', end: '2026-12-31' },
    freshness: 'degraded',
    // Deliberately identical to the first: two regions degraded by the same
    // upstream carry the same sentence.
    limitations: ['ch-bo is running on degraded sources'],
  },
];

function announcement(): HTMLElement {
  return document.querySelector('[data-health-announcement]') as HTMLElement;
}

function announceCount(): number {
  return Number(announcement().getAttribute('data-announce-count'));
}

afterEach(cleanup);

// --- once per change, not per render -----------------------------------------

describe('the disclosure is announced once per state change', () => {
  test('announces once on first render', () => {
    render(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    expect(announceCount()).toBe(1);
    expect(announcement().textContent).toMatch(/older than usual/i);
  });

  test('DOES NOT re-announce when re-rendered with the same state', () => {
    // The failure this prevents: a live region that interrupts a screen-reader
    // user reading the table below it, repeatedly, to tell them something they
    // were already told.
    const { rerender } = render(
      <DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />,
    );
    expect(announceCount()).toBe(1);

    rerender(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    rerender(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);

    expect(announceCount()).toBe(1);
  });

  test('re-announces when the state actually changes', () => {
    const { rerender } = render(
      <DegradationNotice health="healthy" observedAt={OBSERVED} regions={[]} />,
    );
    expect(announceCount()).toBe(1);
    expect(announcement().textContent).toMatch(/up to date/i);

    rerender(<DegradationNotice health="unavailable" observedAt={OBSERVED} regions={REGIONS} />);

    expect(announceCount()).toBe(2);
    expect(announcement().textContent).toMatch(/not accepting new trips/i);
  });

  test('the region is polite, not assertive', () => {
    // Degradation is a disclosure, not an emergency: most of the page is still
    // true. An assertive region interrupts mid-sentence to say "some data is older
    // than usual", which is the fastest way to teach somebody to ignore it.
    render(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    expect(announcement().getAttribute('aria-live')).toBe('polite');
    expect(announcement().getAttribute('role')).not.toBe('alert');
  });
});

// --- REQ-EVID-001 / REQ-EVID-003: the answer says how old it is ---------------

describe('the observation time', () => {
  test('is rendered even when everything is healthy', () => {
    // Showing it only when degraded would make its presence a degradation signal,
    // and would leave the healthy answer — where a stale "all good" does the most
    // damage — with nothing to say how old it is.
    render(<DegradationNotice health="healthy" observedAt={OBSERVED} regions={[]} />);
    expect(document.querySelector(`[data-observed-at="${OBSERVED}"]`)).not.toBeNull();
  });

  test('is a machine-readable time element, not only prose', () => {
    render(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    const time = document.querySelector('time');
    expect(time?.getAttribute('datetime')).toBe(OBSERVED);
  });

  test('says the answer was taken earlier than the request', () => {
    // REQ-EVID-003: an estimate is never rendered as confirmed. Without this
    // sentence a reader has no reason to think the timestamp is not "now".
    render(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    expect(document.body.textContent).toMatch(/not the moment you asked for it/i);
  });

  test('falls back to the raw value rather than rendering Invalid Date', () => {
    render(<DegradationNotice health="healthy" observedAt="not-a-timestamp" regions={[]} />);
    expect(document.body.textContent).toContain('not-a-timestamp');
    expect(document.body.textContent).not.toContain('Invalid Date');
  });
});

// --- the text comes from the read model ---------------------------------------

describe('limitations', () => {
  test('are rendered verbatim from the read model', () => {
    render(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    expect(screen.getByText('ch-bo is running on degraded sources')).toBeTruthy();
  });

  test('are deduplicated, because one fault said twice reads as two', () => {
    render(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    const items = screen.getAllByRole('listitem').map((li) => li.textContent);
    expect(items).toEqual(['ch-bo is running on degraded sources']);
  });

  test('no list is rendered when there is nothing to disclose', () => {
    render(<DegradationNotice health="healthy" observedAt={OBSERVED} regions={[]} />);
    expect(screen.queryByRole('list')).toBeNull();
  });

  test('a region that omits limitations entirely does not crash the banner', () => {
    // `limitations` is OPTIONAL in the contract. Coding to "the handler always
    // sends one" makes this component correct only against today's server.
    const withoutLimitations = [
      { ...REGIONS[0], limitations: undefined },
    ] as unknown as readonly CoverageRegion[];
    render(
      <DegradationNotice health="degraded" observedAt={OBSERVED} regions={withoutLimitations} />,
    );
    expect(screen.queryByRole('list')).toBeNull();
  });
});

// --- REQ-EVID-006: nobody is named --------------------------------------------

describe('no supplier is nameable', () => {
  test('no provider name appears for any health value', () => {
    for (const health of ['healthy', 'degraded', 'unavailable'] as const) {
      cleanup();
      render(<DegradationNotice health={health} observedAt={OBSERVED} regions={REGIONS} />);
      const text = (document.body.textContent ?? '').toLowerCase();
      for (const supplier of ['opentransportdata', 'otd', 'meteoswiss', 'openstreetmap', 'osm']) {
        expect(text, `${health} names ${supplier}`).not.toContain(supplier);
      }
    }
  });

  test('no count of sources is rendered', () => {
    // A count reveals the supply chain's size by another route — the reason
    // `provider_health` is one aggregate label rather than a breakdown.
    render(<DegradationNotice health="degraded" observedAt={OBSERVED} regions={REGIONS} />);
    const text = document.body.textContent ?? '';
    expect(text).not.toMatch(/\b\d+\s+(sources?|providers?|suppliers?)\b/i);
  });
});
