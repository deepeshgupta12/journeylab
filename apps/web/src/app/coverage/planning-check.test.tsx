/**
 * @vitest-environment jsdom
 *
 * Requested per file rather than per package. A package-wide jsdom default breaks
 * `i18n.test.ts`, which reads its own source through `import.meta.url` — see
 * `vitest.config.ts`.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';
import type { CoverageRegion } from './fetch-coverage';
import { PlanningCheck } from './planning-check';

/**
 * STEP-007.03 — the refusal surface (REQ-TRIP-002, REQ-A11Y-001).
 *
 * WHAT ONLY A RENDERED DOCUMENT CAN ANSWER
 *   Which live region an outcome lands in. A refusal shown in a `polite` region is
 *   announced after whatever the screen reader is already saying, which for a
 *   traveller mid-form means several seconds of typing into a request that has
 *   already been refused. Reading the source cannot tell you this; rendering can.
 *
 *   The other property here is negative and matters more: **no partial result on a
 *   refusal.** `test_trip_request.py` proves the server sends none. These prove the
 *   page does not invent one — a component that helpfully rendered a suggested
 *   outline would satisfy every server-side test in the repository.
 */

const REGIONS: readonly CoverageRegion[] = [
  {
    region_id: 'ch-bo',
    display_name: 'Bernese Oberland',
    date_bounds: { start: '2026-01-01', end: '2026-12-31' },
    freshness: 'current',
    limitations: [],
  },
];

function respondWith(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response);
}

/*
 * THE NOTIFICATION REGIONS, NOT "THE LIVE REGIONS".
 *
 * `[aria-live="polite"]` is not unique on this page and the first attempt at these
 * helpers used it. Every `Field` renders its own empty polite error slot, so the
 * form contributes three of them ahead of the notification region — the selector
 * matched a field's error slot, found it empty, and reported that the acceptance
 * had not been announced.
 *
 * That is correct markup, not a bug to fix: a field error belongs to its field and
 * announcing it from a shared region would detach it from the control it describes.
 * It does mean "the polite region" is an ambiguous phrase on any page with a form,
 * so these select the notification regions by the class that identifies them.
 */
function assertiveText(container: HTMLElement): string {
  return container.querySelector('.jl-notifications--assertive')?.textContent?.trim() ?? '';
}

function politeText(container: HTMLElement): string {
  return container.querySelector('.jl-notifications--polite')?.textContent?.trim() ?? '';
}

async function submit(): Promise<void> {
  const { default: userEventDefault } = await import('@testing-library/user-event');
  const user = userEventDefault.setup();
  await user.type(screen.getByLabelText(/first day/i), '2026-10-02');
  await user.type(screen.getByLabelText(/last day/i), '2026-10-06');
  await user.click(screen.getByRole('button', { name: /check these dates/i }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('a refusal is announced, not only shown', () => {
  test('a refusal is rendered into the assertive region', async () => {
    vi.stubGlobal(
      'fetch',
      respondWith(422, {
        code: 'coverage.unsupported_dates',
        detail: 'JourneyLab plans trips of 3 to 7 days. Those dates are 11 days.',
        retryable: false,
        remediation: {
          kind: 'adjust_trip_length',
          supported_trip_days: { minimum: 3, maximum: 7 },
        },
      }),
    );
    const { container } = render(<PlanningCheck regions={REGIONS} />);
    await submit();

    // Asserted on the LIVE REGION, not on `getByRole('alert')`.
    //
    // `NotificationRegion` mounts both regions permanently and empty, which is
    // correct: a screen reader reads `aria-live` when the region is created, not
    // when it mutates, so a region created at the moment of the message announces
    // nothing. That means "an alert exists" is always true and proves nothing —
    // what matters is which region the text landed in.
    await waitFor(() => expect(assertiveText(container)).toMatch(/cannot plan this/i));
    expect(assertiveText(container)).toMatch(/3 to 7 days/i);
    expect(politeText(container)).toBe('');
  });

  test('an acceptance is polite, not assertive', async () => {
    vi.stubGlobal(
      'fetch',
      respondWith(200, {
        region_id: 'ch-bo',
        display_name: 'Bernese Oberland',
        nights: 4,
        disclosures: [],
      }),
    );
    const { container } = render(<PlanningCheck regions={REGIONS} />);
    await submit();

    await waitFor(() => expect(politeText(container)).toMatch(/we can plan this/i));
    // The negative half, and the reason this test exists. Without it the suite
    // passes on a component that shouts every outcome — which is its own
    // accessibility failure: a page that interrupts on success teaches people to
    // ignore the interruptions, including the one that mattered.
    expect(assertiveText(container)).toBe('');
  });

  test('a degradation disclosure is carried into the acceptance', async () => {
    vi.stubGlobal(
      'fetch',
      respondWith(200, {
        region_id: 'ch-bo',
        display_name: 'Bernese Oberland',
        nights: 4,
        disclosures: ['Bernese Oberland is running on degraded sources.'],
      }),
    );
    const { container } = render(<PlanningCheck regions={REGIONS} />);
    await submit();

    await waitFor(() => expect(politeText(container)).toMatch(/running on degraded sources/i));
  });
});

describe('a refusal produces no partial result', () => {
  test('nothing plan-shaped is rendered on a refusal', async () => {
    vi.stubGlobal(
      'fetch',
      respondWith(422, {
        code: 'coverage.unsupported_region',
        detail: 'We do not cover that yet.',
        retryable: false,
        remediation: { kind: 'choose_supported_region' },
      }),
    );
    const { container } = render(<PlanningCheck regions={REGIONS} />);
    await submit();
    await waitFor(() => expect(assertiveText(container)).toMatch(/cannot plan this/i));

    const text = (container.textContent ?? '').toLowerCase();
    for (const shape of ['itinerary', 'day 1', 'suggested trip', 'draft plan', 'scenario']) {
      expect(text).not.toContain(shape);
    }
    // A table would be the most convincing partial result of all — it looks
    // exactly like the answer this page gives when it can answer.
    expect(container.querySelector('table')).toBeNull();
  });

  test('an unreachable service is distinguished from a refusal', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('connect ECONNREFUSED 127.0.0.1:5710')),
    );
    const { container } = render(<PlanningCheck regions={REGIONS} />);
    await submit();

    await waitFor(() => expect(assertiveText(container)).toMatch(/could not check/i));
    expect(assertiveText(container)).toMatch(
      /not a statement that your destination is unsupported/i,
    );
    // The thrown error carries a host and a port and this string is public.
    expect(container.textContent ?? '').not.toContain('5710');
    expect(container.textContent ?? '').not.toContain('ECONNREFUSED');
  });
});

describe('the form does not decide anything itself', () => {
  test('an out-of-bounds request is still sent to the server', async () => {
    // Every bound is in `REGIONS` already, so a component that validated locally
    // would short-circuit here and never call fetch. That is the drift `BUG-029`
    // cost, and it would look like a performance optimisation.
    const fetchMock = respondWith(422, {
      code: 'coverage.unsupported_dates',
      detail: 'Outside the window.',
      retryable: false,
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<PlanningCheck regions={REGIONS} />);

    const { default: userEventDefault } = await import('@testing-library/user-event');
    const user = userEventDefault.setup();
    await user.type(screen.getByLabelText(/first day/i), '2029-01-01');
    await user.type(screen.getByLabelText(/last day/i), '2029-01-04');
    await user.click(screen.getByRole('button', { name: /check these dates/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({
      region_id: 'ch-bo',
      start_date: '2029-01-01',
      end_date: '2029-01-04',
    });
  });

  test('an empty form is not sent, and says why', async () => {
    const fetchMock = respondWith(200, {});
    vi.stubGlobal('fetch', fetchMock);
    render(<PlanningCheck regions={REGIONS} />);

    const { default: userEventDefault } = await import('@testing-library/user-event');
    const user = userEventDefault.setup();
    await user.click(screen.getByRole('button', { name: /check these dates/i }));

    await waitFor(() =>
      expect(screen.getByText(/enter both a start and an end date/i)).toBeTruthy(),
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('with nothing declared', () => {
  test('no form is offered, because there is nothing it could ask about', () => {
    render(<PlanningCheck regions={[]} />);
    expect(screen.queryByRole('button', { name: /check these dates/i })).toBeNull();
    expect(screen.getByText(/there is nothing to check yet/i)).toBeTruthy();
  });
});
