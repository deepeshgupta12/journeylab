/**
 * The nine mandatory quality states — STEP-003.03 (REQ-A11Y-004).
 *
 * FRONTEND_ARCHITECTURE §4: "Every major screen must implement **all** of:
 * skeleton, empty, partial-data, stale-data, provider-down, infeasible,
 * solver-timeout, unauthorized, offline."
 *
 * Declared as data, like the design tokens and the authorization matrix, so a
 * test can assert the set is complete rather than a reviewer counting them.
 * "All nine" is an acceptance criterion; a list in a comment cannot be checked.
 *
 * EVERY STATE CARRIES AN ICON AND TEXT
 *   REQ-A11Y-004 forbids colour as the only signal. A state distinguished purely
 *   by a red or amber tint is invisible to a colour-blind user and to anyone using
 *   forced-colors, which overrides the palette entirely.
 */

export type QualityStateName =
  | 'skeleton'
  | 'empty'
  | 'partial-data'
  | 'stale-data'
  | 'provider-down'
  | 'infeasible'
  | 'solver-timeout'
  | 'unauthorized'
  | 'offline';

export interface QualityState {
  readonly name: QualityStateName;
  /** Non-colour affordance. REQ-A11Y-004. */
  readonly icon: string;
  /** Accessible name. An icon with no text is invisible to a screen reader. */
  readonly label: string;
  /**
   * How assistive technology should learn about it.
   *
   * `polite` for everything that is not a failure of the user's own action.
   * `assertive` is reserved for states that make the current view untrustworthy —
   * interrupting someone mid-sentence is justified only when what they are
   * reading is wrong.
   */
  readonly politeness: 'polite' | 'assertive';
  /** Whether the user can do something about it. Drives the retry affordance. */
  readonly recoverable: boolean;
}

export const QUALITY_STATES: readonly QualityState[] = [
  {
    name: 'skeleton',
    icon: 'loading',
    label: 'Loading',
    politeness: 'polite',
    recoverable: false,
  },
  {
    name: 'empty',
    icon: 'inbox',
    label: 'Nothing here yet',
    politeness: 'polite',
    recoverable: false,
  },
  {
    name: 'partial-data',
    icon: 'alert-triangle',
    label: 'Some data is missing',
    politeness: 'polite',
    recoverable: true,
  },
  {
    name: 'stale-data',
    icon: 'clock',
    label: 'Last checked',
    politeness: 'polite',
    recoverable: true,
  },
  {
    name: 'provider-down',
    icon: 'plug-off',
    label: 'A data source is unavailable',
    politeness: 'polite',
    recoverable: true,
  },
  {
    // NOT an error state. REQ-CONS-005 and FRONTEND_ARCHITECTURE §4: infeasible is
    // first-class, showing the minimal conflict set and suggested relaxations. A
    // toast saying "failed" tells the traveller nothing about WHICH constraints
    // cannot hold together, which is the only useful information here.
    name: 'infeasible',
    icon: 'x-octagon',
    label: 'These constraints cannot all hold',
    politeness: 'assertive',
    recoverable: true,
  },
  {
    name: 'solver-timeout',
    icon: 'hourglass',
    label: 'Took too long to finish',
    politeness: 'polite',
    recoverable: true,
  },
  {
    name: 'unauthorized',
    icon: 'lock',
    label: 'Not available',
    politeness: 'assertive',
    recoverable: false,
  },
  {
    name: 'offline',
    icon: 'cloud-off',
    label: 'Offline',
    politeness: 'assertive',
    recoverable: true,
  },
] as const;

/** Every state named by FRONTEND_ARCHITECTURE §4, for completeness assertions. */
export const REQUIRED_STATE_NAMES: readonly QualityStateName[] = [
  'skeleton',
  'empty',
  'partial-data',
  'stale-data',
  'provider-down',
  'infeasible',
  'solver-timeout',
  'unauthorized',
  'offline',
] as const;

export function qualityState(name: QualityStateName): QualityState {
  const found = QUALITY_STATES.find((state) => state.name === name);
  if (!found) {
    // Unreachable through the type system, but a missing state must not silently
    // render as a blank region — that is indistinguishable from success.
    throw new Error(`unknown quality state: ${name}`);
  }
  return found;
}
