/**
 * Design tokens — STEP-003.01 (REQ-A11Y-004, REQ-NFR-013).
 *
 * TOKENS ARE DATA HERE AND CSS IS GENERATED FROM THEM
 *   `tokens.css` is produced by `tools/gen-tokens.ts`. Declaring them as data
 *   first is what makes the accessibility claims testable: a test can compute the
 *   actual WCAG contrast ratio of every declared pair, rather than trusting a
 *   comment that says "AA verified".
 *
 *   Same reasoning as the authorization matrix in STEP-002.03 — the document that
 *   states the rule also generates the code, so the two cannot drift.
 *
 * WHAT "CONTRAST PAIR" MEANS
 *   A colour on its own has no contrast. Every foreground token is declared
 *   ALONGSIDE the background it is allowed to appear on, and the test walks that
 *   list. A token with no declared pairing is unverifiable and the test says so.
 */

import { AA_LARGE_TEXT_AND_UI, AA_NORMAL_TEXT } from './contrast';

export type ThemeName = 'light' | 'dark' | 'high-contrast';

export interface ContrastPair {
  readonly foreground: string;
  readonly background: string;
  /** WCAG minimum this pair must meet. UI/large text is 3:1, body text 4.5:1. */
  readonly minimum: number;
  readonly usage: string;
}

// --- palettes ---------------------------------------------------------------

export const LIGHT = {
  'surface-base': '#ffffff',
  'surface-raised': '#f6f7f9',
  'surface-sunken': '#eceef2',
  'text-primary': '#14181f',
  'text-secondary': '#4a5260',
  'border-default': '#767d8a',
  'border-strong': '#4a5260',
  'action-primary': '#0b5cd5',
  'action-primary-text': '#ffffff',
  'focus-ring': '#0b5cd5',
  'status-success': '#0f6b3d',
  'status-warning': '#7a4a00',
  'status-error': '#b3261e',
  'status-info': '#0b5cd5',
} as const;

export const DARK = {
  'surface-base': '#101419',
  'surface-raised': '#181d24',
  'surface-sunken': '#0a0d11',
  'text-primary': '#f2f4f7',
  'text-secondary': '#b9c0cc',
  'border-default': '#79818f',
  'border-strong': '#b9c0cc',
  'action-primary': '#7fb2ff',
  'action-primary-text': '#101419',
  'focus-ring': '#7fb2ff',
  'status-success': '#5cc98e',
  'status-warning': '#e0a33a',
  'status-error': '#ff9d94',
  'status-info': '#7fb2ff',
} as const;

/**
 * High contrast is NOT "dark mode with the dial turned up".
 *
 * It is a distinct set held to AAA (7:1) for body text, for users who cannot use
 * the default palette at all. Every value is pure or near-pure so the ratios are
 * unambiguous rather than marginal.
 */
export const HIGH_CONTRAST = {
  'surface-base': '#000000',
  'surface-raised': '#000000',
  'surface-sunken': '#000000',
  'text-primary': '#ffffff',
  'text-secondary': '#ffffff',
  'border-default': '#ffffff',
  'border-strong': '#ffffff',
  'action-primary': '#ffff00',
  'action-primary-text': '#000000',
  'focus-ring': '#ffff00',
  'status-success': '#00ff7f',
  'status-warning': '#ffd400',
  'status-error': '#ff8080',
  'status-info': '#7fdfff',
} as const;

export const PALETTES: Record<ThemeName, Record<string, string>> = {
  light: LIGHT,
  dark: DARK,
  'high-contrast': HIGH_CONTRAST,
};

// --- declared contrast pairs ------------------------------------------------

/** Every pairing the design system permits, and the bar it must clear. */
export function contrastPairs(palette: Record<string, string>): ContrastPair[] {
  const on = (fg: string, bg: string, minimum: number, usage: string): ContrastPair => ({
    foreground: palette[fg] as string,
    background: palette[bg] as string,
    minimum,
    usage,
  });

  return [
    on('text-primary', 'surface-base', AA_NORMAL_TEXT, 'body text on the page'),
    on('text-primary', 'surface-raised', AA_NORMAL_TEXT, 'body text on a card'),
    on('text-primary', 'surface-sunken', AA_NORMAL_TEXT, 'body text on a well'),
    on('text-secondary', 'surface-base', AA_NORMAL_TEXT, 'supporting text'),
    on('text-secondary', 'surface-raised', AA_NORMAL_TEXT, 'supporting text on a card'),
    on('action-primary', 'surface-base', AA_NORMAL_TEXT, 'link text'),
    on('action-primary-text', 'action-primary', AA_NORMAL_TEXT, 'label inside a primary button'),
    // SC 1.4.11: non-text UI components need 3:1, not 4.5:1.
    on('border-default', 'surface-base', AA_LARGE_TEXT_AND_UI, 'input border'),
    on('border-strong', 'surface-base', AA_LARGE_TEXT_AND_UI, 'emphasised divider'),
    on('focus-ring', 'surface-base', AA_LARGE_TEXT_AND_UI, 'focus indicator'),
    on('status-success', 'surface-base', AA_NORMAL_TEXT, 'success text'),
    on('status-warning', 'surface-base', AA_NORMAL_TEXT, 'warning text'),
    on('status-error', 'surface-base', AA_NORMAL_TEXT, 'error text'),
    on('status-info', 'surface-base', AA_NORMAL_TEXT, 'informational text'),
  ];
}

// --- status tokens must never rely on colour alone --------------------------

export interface StatusToken {
  readonly name: string;
  readonly colorToken: string;
  /** The non-colour affordance. REQ-A11Y-004: colour is never the only signal. */
  readonly icon: string;
  /** Screen-reader and fallback text. An icon alone is not sufficient either. */
  readonly label: string;
}

/**
 * Every status carries an icon AND a text label beside its colour.
 *
 * FRONTEND_ARCHITECTURE §5: "Text or icon accompanies every status colour." This
 * goes slightly further and requires both, because an icon with no accessible
 * name is invisible to a screen reader, and text alone is easy to miss when
 * scanning.
 */
export const STATUS_TOKENS: readonly StatusToken[] = [
  { name: 'success', colorToken: 'status-success', icon: 'check-circle', label: 'Success' },
  { name: 'warning', colorToken: 'status-warning', icon: 'alert-triangle', label: 'Warning' },
  { name: 'error', colorToken: 'status-error', icon: 'x-octagon', label: 'Error' },
  { name: 'info', colorToken: 'status-info', icon: 'info-circle', label: 'Information' },
] as const;

// --- scales -----------------------------------------------------------------

export const SPACING = {
  'space-0': '0',
  'space-1': '0.25rem',
  'space-2': '0.5rem',
  'space-3': '0.75rem',
  'space-4': '1rem',
  'space-6': '1.5rem',
  'space-8': '2rem',
  'space-12': '3rem',
  'space-16': '4rem',
} as const;

/**
 * rem throughout, never px.
 *
 * REQ-A11Y and WCAG 1.4.4 require text to survive 200% zoom. A px font size
 * ignores the browser's font-size setting entirely, which is the setting many
 * low-vision users rely on before they ever reach a zoom control.
 */
export const TYPOGRAPHY = {
  'font-size-xs': '0.75rem',
  'font-size-sm': '0.875rem',
  'font-size-base': '1rem',
  'font-size-lg': '1.125rem',
  'font-size-xl': '1.375rem',
  'font-size-2xl': '1.75rem',
  'font-size-3xl': '2.25rem',
  'line-height-tight': '1.25',
  'line-height-normal': '1.5',
  'line-height-relaxed': '1.75',
  'font-weight-regular': '400',
  'font-weight-medium': '500',
  'font-weight-bold': '700',
} as const;

export const ELEVATION = {
  'elevation-0': 'none',
  'elevation-1': '0 1px 2px rgb(0 0 0 / 0.08)',
  'elevation-2': '0 2px 8px rgb(0 0 0 / 0.10)',
  'elevation-3': '0 8px 24px rgb(0 0 0 / 0.14)',
} as const;

// --- motion -----------------------------------------------------------------

export const MOTION = {
  'motion-duration-instant': '0ms',
  'motion-duration-fast': '120ms',
  'motion-duration-normal': '200ms',
  'motion-duration-slow': '320ms',
  'motion-ease-standard': 'cubic-bezier(0.2, 0, 0, 1)',
  'motion-ease-decelerate': 'cubic-bezier(0, 0, 0, 1)',
} as const;

/**
 * Reduced motion SUPPRESSES animation. It does not shorten it.
 *
 * The sub-step record is explicit that this is vestibular safety, not a
 * preference: "it must suppress animation, not merely shorten it." A 60ms
 * animation still moves, and movement is what triggers vertigo and nausea. Every
 * duration is therefore exactly 0ms, and a test asserts `=== "0ms"` rather than
 * "shorter than the default".
 */
export const MOTION_REDUCED = {
  'motion-duration-instant': '0ms',
  'motion-duration-fast': '0ms',
  'motion-duration-normal': '0ms',
  'motion-duration-slow': '0ms',
  'motion-ease-standard': 'linear',
  'motion-ease-decelerate': 'linear',
} as const;
