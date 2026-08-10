/**
 * Runtime accessibility counter — TST-A11Y-001 · STEP-003.08.
 *
 * The counter is the part of the accessibility story that runs where the users
 * are. These tests establish that it counts the right things, reports nothing
 * identifying, and cannot take the page down when telemetry fails.
 */

import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  type A11yEvent,
  countUnnamedControls,
  createA11yCounter,
  observeFocusLoss,
} from './counter';

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('counter', () => {
  it('accumulates per signal and surface', () => {
    const c = createA11yCounter();
    c.count('focus-lost', '/trips');
    c.count('focus-lost', '/trips');
    c.count('name-missing', '/trips');
    expect(c.snapshot()).toEqual({ 'focus-lost:/trips': 2, 'name-missing:/trips': 1 });
  });

  it('forwards to the sink with NO identifying payload', () => {
    // A control's accessible name can contain a traveller's name or destination.
    // The event carries a signal and a surface label, and nothing else — asserted
    // structurally so a future field cannot be added without this failing.
    const events: A11yEvent[] = [];
    const c = createA11yCounter((e) => events.push(e));
    c.count('focus-lost', '/trips/[id]');
    expect(events).toHaveLength(1);
    expect(Object.keys(events[0] as object).sort()).toEqual(['signal', 'surface']);
    expect(events[0]?.surface).toBe('/trips/[id]');
  });

  it('keeps counting when the sink throws', () => {
    // A metrics endpoint being down is not a reason to show a traveller an error.
    const c = createA11yCounter(() => {
      throw new Error('collector unreachable');
    });
    expect(() => c.count('focus-lost', '/')).not.toThrow();
    expect(c.snapshot()['focus-lost:/']).toBe(1);
  });

  it('does not share state between instances', () => {
    // Server-rendered code runs many requests in one process; a module-level
    // counter would attribute one tenant's signals to another.
    const a = createA11yCounter();
    const b = createA11yCounter();
    a.count('focus-lost', '/');
    expect(b.snapshot()).toEqual({});
  });
});

describe('focus-loss observer', () => {
  it('counts when focus falls to body after a navigation', () => {
    vi.useFakeTimers();
    const c = createA11yCounter();
    const stop = observeFocusLoss(c, () => '/trips', { graceMs: 10 });

    document.body.innerHTML = '<p>content with nothing focusable</p>';
    document.dispatchEvent(new Event('journeylab:navigated'));
    vi.advanceTimersByTime(20);

    expect(c.snapshot()['focus-lost:/trips']).toBe(1);
    stop();
  });

  it('does NOT count when focus landed somewhere real', () => {
    vi.useFakeTimers();
    const c = createA11yCounter();
    const stop = observeFocusLoss(c, () => '/trips', { graceMs: 10 });

    document.body.innerHTML = '<main tabindex="-1" id="m">x</main>';
    document.getElementById('m')?.focus();
    document.dispatchEvent(new Event('journeylab:navigated'));
    vi.advanceTimersByTime(20);

    expect(c.snapshot()).toEqual({});
    stop();
  });

  it('stops observing when disposed', () => {
    // The caller owns the lifetime. A component that unmounts must not keep
    // reporting for a surface that is no longer on screen.
    vi.useFakeTimers();
    const c = createA11yCounter();
    const stop = observeFocusLoss(c, () => '/trips', { graceMs: 10 });
    stop();

    document.dispatchEvent(new Event('journeylab:navigated'));
    vi.advanceTimersByTime(20);
    expect(c.snapshot()).toEqual({});
  });

  it('is inert with no document rather than throwing', () => {
    // It is imported by server code too; a server render must not explode.
    const c = createA11yCounter();
    const stop = observeFocusLoss(c, () => '/', { doc: undefined as unknown as Document });
    expect(() => stop()).not.toThrow();
  });
});

describe('unnamed control detection', () => {
  function root(html: string): HTMLElement {
    const el = document.createElement('div');
    el.innerHTML = html;
    document.body.append(el);
    return el;
  }

  it('finds a button with no name', () => {
    const c = createA11yCounter();
    const el = root('<button type="button"></button>');
    expect(countUnnamedControls(el, c, '/x')).toBe(1);
    expect(c.snapshot()['name-missing:/x']).toBe(1);
  });

  it('accepts every normal way of providing a name', () => {
    const c = createA11yCounter();
    const el = root(`
      <button type="button">Text content</button>
      <button type="button" aria-label="Labelled"></button>
      <span id="lbl">Referenced</span><button type="button" aria-labelledby="lbl"></button>
      <label for="i">Field</label><input id="i" />
      <label>Wrapping <input /></label>
    `);
    expect(countUnnamedControls(el, c, '/x')).toBe(0);
  });

  it('ignores hidden inputs and aria-hidden controls', () => {
    const c = createA11yCounter();
    const el = root('<input type="hidden" /><button type="button" aria-hidden="true"></button>');
    expect(countUnnamedControls(el, c, '/x')).toBe(0);
  });
});
