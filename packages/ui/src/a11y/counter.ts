/**
 * Runtime accessibility failure counter — STEP-003.08 (REQ-A11Y-001).
 *
 * WHAT THIS IS NOT
 *   It is not axe in production. axe walks the whole accessibility tree on every
 *   run; doing that on a traveller's phone would cost more than the page. It also
 *   would not help — a violation detected on the device is already in front of
 *   the user.
 *
 * WHAT IT IS
 *   A counter for the small set of accessibility failures that are (a) cheap to
 *   observe from inside the application and (b) invisible to a static scan
 *   because they only occur in a real session:
 *
 *     focus-lost          After a client-side navigation, focus fell to <body>.
 *                         The keyboard user is now at the top of the document
 *                         with no idea where they are. axe cannot see this: it
 *                         is a property of a transition, not of a page.
 *
 *     name-missing        A control was rendered with no accessible name. axe
 *                         catches this on scanned surfaces; production catches it
 *                         on surfaces nobody thought to scan.
 *
 *     live-region-empty   A status message was written to a region that is not a
 *                         live region, so nothing was announced.
 *
 *   The value is the trend. One `focus-lost` is a bug report; a jump after a
 *   release is a regression nobody filed.
 *
 * PRIVACY
 *   The payload is a signal name and a caller-supplied surface label. **No
 *   element text, no ids, no URLs, no user identifier.** A control's accessible
 *   name can contain a traveller's name or a destination, so it is deliberately
 *   not reported — the count says something needs a look, and the developer
 *   reproduces it. `REQ-PRIV-003`: nothing here infers anything about anyone.
 */

export type A11ySignal = 'focus-lost' | 'name-missing' | 'live-region-empty';

export interface A11yEvent {
  readonly signal: A11ySignal;
  /**
   * A stable, low-cardinality label for where this happened — a route pattern,
   * not a URL. `/trips/[id]`, never `/trips/9f3c…`, which would be an identifier
   * in telemetry and a cardinality explosion in the metrics backend.
   */
  readonly surface: string;
}

export type A11ySink = (event: A11yEvent) => void;

export interface A11yCounter {
  readonly count: (signal: A11ySignal, surface: string) => void;
  /** Current totals, keyed `signal:surface`. For tests and local diagnostics. */
  readonly snapshot: () => Readonly<Record<string, number>>;
  readonly reset: () => void;
}

/**
 * A counter instance.
 *
 * An instance, not a module-level singleton. Server-rendered code runs many
 * requests concurrently in one process, and a shared mutable counter there
 * attributes one tenant's signals to another — the same hazard the i18n
 * catalogue avoided at STEP-003.07.
 */
export function createA11yCounter(sink?: A11ySink): A11yCounter {
  const totals = new Map<string, number>();
  return {
    count(signal, surface) {
      const key = `${signal}:${surface}`;
      totals.set(key, (totals.get(key) ?? 0) + 1);
      // The sink is called after the local total is updated, so a throwing sink
      // cannot lose the count. Telemetry failing must never break the page.
      try {
        sink?.({ signal, surface });
      } catch {
        // Deliberately swallowed. A metrics endpoint being down is not a reason
        // to show a traveller an error.
      }
    },
    snapshot: () => Object.fromEntries(totals),
    reset: () => totals.clear(),
  };
}

/** Elements that can hold focus and are therefore valid landing places. */
const FOCUSABLE = 'a[href],button,input,select,textarea,[tabindex],[role="dialog"],main,h1';

/**
 * Watch for focus falling to `<body>` after a route change.
 *
 * WHY `<body>` IS THE SIGNAL
 *   When a client-side navigation replaces the DOM, the element that had focus is
 *   removed and the browser reparents focus to `document.body`. For a sighted
 *   user nothing happens. For a keyboard user the next Tab starts from the top of
 *   the document, and for a screen-reader user nothing is announced at all — the
 *   page changed and they were not told.
 *
 *   Returns a disposer. The caller owns the lifetime; nothing is registered
 *   globally, so a component that unmounts stops observing.
 */
export function observeFocusLoss(
  counter: A11yCounter,
  surface: () => string,
  options: { readonly graceMs?: number; readonly doc?: Document } = {},
): () => void {
  const doc = options.doc ?? globalThis.document;
  if (doc === undefined) return () => undefined;

  // A grace period, because focus legitimately passes through body for a frame
  // during a transition. Counting that would make the metric noise.
  const grace = options.graceMs ?? 300;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const check = () => {
    timer = setTimeout(() => {
      const active = doc.activeElement;
      const landed = active !== null && active !== doc.body && active.matches?.(FOCUSABLE);
      if (!landed) counter.count('focus-lost', surface());
    }, grace);
  };

  doc.addEventListener('journeylab:navigated', check);
  return () => {
    if (timer !== undefined) clearTimeout(timer);
    doc.removeEventListener('journeylab:navigated', check);
  };
}

/**
 * Count controls rendered with no accessible name, within one container.
 *
 * A cheap approximation of one axe rule, not a replacement for axe: it checks the
 * four ways a name is normally provided and nothing else. It is here because it
 * can run on surfaces the CI scan never visits — a route behind a role, a state
 * only a real provider failure produces.
 */
export function countUnnamedControls(
  root: ParentNode,
  counter: A11yCounter,
  surface: string,
): number {
  const controls = root.querySelectorAll<HTMLElement>('button,a[href],input,select,textarea');
  let unnamed = 0;
  for (const el of Array.from(controls)) {
    if (el.getAttribute('aria-hidden') === 'true') continue;
    if (el.hasAttribute('aria-label') || el.hasAttribute('aria-labelledby')) continue;
    if (el.id !== '' && root.querySelector(`label[for="${CSS.escape(el.id)}"]`) !== null) continue;
    if (el.closest('label') !== null) continue;
    if ((el.textContent?.trim().length ?? 0) > 0) continue;
    if (el instanceof HTMLInputElement && el.type === 'hidden') continue;
    unnamed += 1;
    counter.count('name-missing', surface);
  }
  return unnamed;
}
