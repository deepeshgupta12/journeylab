/**
 * Form primitive accessibility — TST-A11Y-001 · STEP-003.02.
 *
 * The axe runs are the acceptance criterion ("zero AA violations"), but they are
 * a floor, not a ceiling: axe cannot detect focus theft, cannot tell a polite
 * live region from an assertive one in practice, and cannot know that a date
 * string means a different instant in Auckland. Those are asserted directly.
 */

import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { afterEach, describe, expect, it } from 'vitest';

import { Checkbox, DateInput, NumberInput, RadioGroup, Select, TextInput } from './inputs.tsx';
import { formatLocaleNumber, parseLocaleNumber, separatorsFor } from './locale-number.ts';
import { isValidTimeZone, parseCalendarDate, startOfDayUtc } from './zoned-date.ts';

afterEach(cleanup);

async function axeViolations(container: HTMLElement): Promise<axe.Result[]> {
  const results = await axe.run(container, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
  });
  return results.violations;
}

// --- META: axe must be able to fail, or the runs below prove nothing ---------

describe('axe itself', () => {
  it('detects a missing label', async () => {
    // Without this, "zero violations" is indistinguishable from axe not running.
    const { container } = render(<input type="text" />);
    expect((await axeViolations(container)).map((v) => v.id)).toContain('label');
  });

  it('detects a missing image alt', async () => {
    // The missing alt is the point: this proves axe reports a violation it should.
    // Adding alt would make the assertion below pass for the wrong reason.
    // biome-ignore lint/a11y/useAltText: deliberate violation under test
    const { container } = render(<img src="x.png" />);
    expect((await axeViolations(container)).map((v) => v.id)).toContain('image-alt');
  });
});

// --- acceptance: zero AA violations on every primitive ----------------------

describe('axe — zero WCAG AA violations', () => {
  const cases: Array<[string, () => React.ReactElement]> = [
    ['TextInput', () => <TextInput label="Trip name" />],
    [
      'TextInput with description and error',
      () => <TextInput label="Trip name" description="Shown to collaborators" error="Required" />,
    ],
    [
      'NumberInput',
      () => <NumberInput label="Budget" locale="en-GB" value="" onValueChange={() => {}} />,
    ],
    ['DateInput', () => <DateInput label="Start date" value="" onDateChange={() => {}} />],
    [
      'Select',
      () => (
        <Select
          label="Pace"
          options={[
            { value: 'relaxed', label: 'Relaxed' },
            { value: 'packed', label: 'Packed' },
          ]}
        />
      ),
    ],
    ['Checkbox', () => <Checkbox label="Step-free access required" />],
    [
      'RadioGroup',
      () => (
        <RadioGroup
          label="Trip pace"
          name="pace"
          options={[
            { value: 'relaxed', label: 'Relaxed' },
            { value: 'packed', label: 'Packed' },
          ]}
        />
      ),
    ],
  ];

  it.each(cases)('%s', async (_name, element) => {
    const { container } = render(element());
    const violations = await axeViolations(container);
    expect(
      violations.map((v) => `${v.id}: ${v.help}`),
      'axe reported WCAG AA violations',
    ).toEqual([]);
  });
});

// --- programmatic association ------------------------------------------------

describe('label, description and error association', () => {
  it('associates the label with the control', () => {
    render(<TextInput label="Trip name" />);
    // getByLabelText only succeeds when the association is real.
    expect(screen.getByLabelText('Trip name')).toBeDefined();
  });

  it('points aria-describedby at BOTH description and error', () => {
    render(<TextInput label="Budget" description="Per person" error="Must be a number" />);
    const input = screen.getByLabelText('Budget');
    const describedBy = input.getAttribute('aria-describedby') ?? '';
    const ids = describedBy.split(' ').filter(Boolean);
    expect(ids.length, `aria-describedby was "${describedBy}"`).toBe(2);

    const texts = ids.map((id) => document.getElementById(id)?.textContent);
    expect(texts).toContain('Per person');
    expect(texts).toContain('Must be a number');
  });

  it('omits aria-invalid entirely when valid, rather than setting it false', () => {
    // Some screen readers announce the attribute's presence regardless of value.
    render(<TextInput label="Trip name" />);
    expect(screen.getByLabelText('Trip name').hasAttribute('aria-invalid')).toBe(false);
  });

  it('sets aria-invalid when an error is present', () => {
    render(<TextInput label="Trip name" error="Required" />);
    expect(screen.getByLabelText('Trip name').getAttribute('aria-invalid')).toBe('true');
  });

  it('announces the required state to assistive technology, not just with an asterisk', () => {
    render(<TextInput label="Trip name" required />);
    // The NATIVE required attribute, not aria-required: input has an ARIA role
    // mapping for it already, and aria-required is unsupported on some input types.
    expect(screen.getByLabelText(/Trip name/).hasAttribute('required')).toBe(true);
    expect(screen.getByText('(required)', { exact: false })).toBeDefined();
  });
});

// --- errors announced politely, without focus theft -------------------------

describe('error announcement', () => {
  it('uses a POLITE live region, never assertive', () => {
    const { container } = render(<TextInput label="Budget" error="Must be a number" />);
    const region = container.querySelector('[aria-live]');
    // role="alert" / aria-live="assertive" interrupts the user mid-sentence.
    expect(region?.getAttribute('aria-live')).toBe('polite');
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });

  it('renders the live region even when there is no error yet', () => {
    // A live region inserted at the moment it gains content is frequently not
    // announced at all — the screen reader must already be observing the node.
    const { container } = render(<TextInput label="Budget" />);
    expect(container.querySelector('[aria-live="polite"]')).not.toBeNull();
  });

  it('does not steal focus when an error appears', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <>
        <TextInput label="Budget" />
        <TextInput label="Notes" />
      </>,
    );
    const notes = screen.getByLabelText('Notes');
    await user.click(notes);
    expect(document.activeElement).toBe(notes);

    rerender(
      <>
        <TextInput label="Budget" error="Must be a number" />
        <TextInput label="Notes" />
      </>,
    );
    expect(
      document.activeElement,
      'focus moved when an error appeared, trapping the keyboard user',
    ).toBe(notes);
  });
});

// --- keyboard completeness ---------------------------------------------------

describe('keyboard', () => {
  it('reaches every primitive by Tab alone', async () => {
    const user = userEvent.setup();
    render(
      <>
        <TextInput label="Trip name" />
        <Select label="Pace" options={[{ value: 'a', label: 'A' }]} />
        <Checkbox label="Step-free" />
      </>,
    );
    await user.tab();
    expect(document.activeElement).toBe(screen.getByLabelText('Trip name'));
    await user.tab();
    expect(document.activeElement).toBe(screen.getByLabelText('Pace'));
    await user.tab();
    expect(document.activeElement).toBe(screen.getByLabelText('Step-free'));
  });

  it('keeps a READ-ONLY field focusable, unlike a disabled one', async () => {
    const user = userEvent.setup();
    render(
      <>
        <TextInput label="Reference" readOnly value="JL-1" onChange={() => {}} />
        <TextInput label="Notes" />
      </>,
    );
    await user.tab();
    // Read-only keeps the value discoverable; disabled would hide it from users
    // who have no other way to read it.
    expect(document.activeElement).toBe(screen.getByLabelText('Reference'));
  });

  it('skips a DISABLED field in the tab order', async () => {
    const user = userEvent.setup();
    render(
      <>
        <TextInput label="Reference" disabled />
        <TextInput label="Notes" />
      </>,
    );
    await user.tab();
    expect(document.activeElement).toBe(screen.getByLabelText('Notes'));
  });
});

// --- locale-aware numeric entry ----------------------------------------------

describe('locale numbers', () => {
  it('derives separators from the locale rather than assuming', () => {
    expect(separatorsFor('en-GB')).toEqual({ group: ',', decimal: '.' });
    expect(separatorsFor('de-DE')).toEqual({ group: '.', decimal: ',' });
  });

  it('parses the same string differently per locale, as it must', () => {
    // This is the whole point. Number.parseFloat("1.234,56") returns 1.234 —
    // wrong by three orders of magnitude, and silently.
    expect(parseLocaleNumber('1.234,56', 'de-DE')).toEqual({ ok: true, value: 1234.56 });
    expect(parseLocaleNumber('1,234.56', 'en-GB')).toEqual({ ok: true, value: 1234.56 });
  });

  it('round-trips through formatting', () => {
    for (const locale of ['en-GB', 'de-DE', 'fr-FR']) {
      const formatted = formatLocaleNumber(1234.56, locale);
      const parsed = parseLocaleNumber(formatted, locale);
      expect(parsed, `${locale}: "${formatted}" did not round-trip`).toEqual({
        ok: true,
        value: 1234.56,
      });
    }
  });

  it('REFUSES an ambiguous grouping rather than guessing', () => {
    // "1,23" is not a valid en-GB grouping and is far more likely to be someone
    // typing a decimal with the wrong separator. Guessing is wrong 50% of the time.
    expect(parseLocaleNumber('1,23', 'en-GB')).toEqual({ ok: false, reason: 'ambiguous' });
  });

  it('returns a result rather than NaN', () => {
    // NaN propagates silently through arithmetic and surfaces far from its cause.
    expect(parseLocaleNumber('abc', 'en-GB').ok).toBe(false);
    expect(parseLocaleNumber('', 'en-GB')).toEqual({ ok: false, reason: 'empty' });
    expect(parseLocaleNumber('1.2.3', 'en-GB').ok).toBe(false);
  });

  it('accepts negatives and bare decimals', () => {
    expect(parseLocaleNumber('-42', 'en-GB')).toEqual({ ok: true, value: -42 });
    expect(parseLocaleNumber('0.5', 'en-GB')).toEqual({ ok: true, value: 0.5 });
  });

  it('uses type=text with inputMode, not type=number', () => {
    // A native number input silently discards characters it considers invalid.
    render(<NumberInput label="Budget" locale="de-DE" value="" onValueChange={() => {}} />);
    const input = screen.getByLabelText('Budget');
    expect(input.getAttribute('type')).toBe('text');
    expect(input.getAttribute('inputmode')).toBe('decimal');
  });

  it('reports both the raw text and the parsed value', async () => {
    const user = userEvent.setup();
    const seen: Array<[string, number | undefined]> = [];
    render(
      <NumberInput
        label="Budget"
        locale="de-DE"
        value=""
        onValueChange={(raw, parsed) => seen.push([raw, parsed])}
      />,
    );
    await user.type(screen.getByLabelText('Budget'), '5');
    expect(seen.at(-1)).toEqual(['5', 5]);
  });
});

// --- dates carry no implicit time zone --------------------------------------

describe('dates', () => {
  it('parses an ISO date into a calendar date, not an instant', () => {
    const result = parseCalendarDate('2026-08-06');
    expect(result).toEqual({ ok: true, date: { year: 2026, month: 8, day: 6 } });
  });

  it('rejects an impossible date instead of rolling it forward', () => {
    // `new Date(2026, 1, 30)` silently becomes 2 March.
    expect(parseCalendarDate('2026-02-30')).toEqual({ ok: false, reason: 'impossible' });
  });

  it('rejects malformed input', () => {
    expect(parseCalendarDate('06/08/2026').ok).toBe(false);
    expect(parseCalendarDate('').ok).toBe(false);
  });

  it('yields a DIFFERENT instant per time zone for the same calendar date', () => {
    // The bug this prevents: the same trip start date meaning two different
    // moments depending on where the reader is.
    const date = { year: 2026, month: 8, day: 6 };
    const auckland = startOfDayUtc(date, 'Pacific/Auckland');
    const london = startOfDayUtc(date, 'Europe/London');
    const utc = startOfDayUtc(date, 'UTC');

    expect(auckland.getTime()).not.toBe(london.getTime());
    expect(auckland.getTime()).toBeLessThan(utc.getTime()); // ahead of UTC
    expect(london.getTime()).toBeLessThan(utc.getTime()); // BST in August
  });

  it('lands on local midnight in the target zone', () => {
    for (const zone of ['UTC', 'Europe/London', 'Pacific/Auckland', 'America/New_York']) {
      const instant = startOfDayUtc({ year: 2026, month: 8, day: 6 }, zone);
      const shown = new Intl.DateTimeFormat('en-CA', {
        timeZone: zone,
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }).format(instant);
      expect(shown, `${zone} did not land on midnight`).toMatch(/^(00|24):00$/);
    }
  });

  it('handles a DST boundary without drifting an hour', () => {
    // 2026-03-29 is when Europe/London springs forward.
    const instant = startOfDayUtc({ year: 2026, month: 3, day: 29 }, 'Europe/London');
    const shown = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Europe/London',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(instant);
    expect(shown).toMatch(/^(00|24):00$/);
  });

  it('validates IANA zones', () => {
    expect(isValidTimeZone('Europe/London')).toBe(true);
    expect(isValidTimeZone('Middle/Earth')).toBe(false);
  });

  it('hands the caller a CalendarDate, never a Date', async () => {
    const user = userEvent.setup();
    const seen: Array<unknown> = [];
    render(<DateInput label="Start" value="" onDateChange={(_raw, parsed) => seen.push(parsed)} />);
    await user.type(screen.getByLabelText('Start'), '2026-08-06');
    const last = seen.at(-1);
    expect(last).not.toBeInstanceOf(Date);
    expect(last).toEqual({ year: 2026, month: 8, day: 6 });
  });
});

// --- radio groups ------------------------------------------------------------

describe('radio group', () => {
  it('uses a fieldset and legend so the question is announced', () => {
    const { container } = render(
      <RadioGroup label="Trip pace" name="pace" options={[{ value: 'a', label: 'Relaxed' }]} />,
    );
    // Without this, a screen reader says "Relaxed, radio button" with no
    // indication of what is being asked.
    expect(container.querySelector('fieldset')).not.toBeNull();
    expect(container.querySelector('legend')?.textContent).toContain('Trip pace');
  });

  it('marks the group required via the native radio attribute, not ARIA', () => {
    // Per the HTML spec, `required` on one radio makes its same-named group
    // required. A fieldset cannot carry aria-required (role="group" does not
    // support it), and forcing role="radiogroup" onto it trades one violation
    // for another.
    render(<RadioGroup label="Pace" name="pace" required options={[{ value: 'a', label: 'A' }]} />);
    expect(screen.getByLabelText('A').hasAttribute('required')).toBe(true);
  });

  it('labels each option individually', () => {
    render(
      <RadioGroup
        label="Trip pace"
        name="pace"
        options={[
          { value: 'relaxed', label: 'Relaxed' },
          { value: 'packed', label: 'Packed' },
        ]}
      />,
    );
    expect(screen.getByLabelText('Relaxed')).toBeDefined();
    expect(screen.getByLabelText('Packed')).toBeDefined();
  });
});
