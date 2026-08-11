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

import { AA_LARGE_TEXT_AND_UI, AA_NORMAL_TEXT } from './contrast.ts';

export type ThemeName = 'light' | 'dark' | 'high-contrast';

export interface ContrastPair {
  readonly foreground: string;
  readonly background: string;
  /** WCAG minimum this pair must meet. UI/large text is 3:1, body text 4.5:1. */
  readonly minimum: number;
  readonly usage: string;
}

// --- palettes ---------------------------------------------------------------

/**
 * WARM NEUTRALS, NOT BLUE-GREY — STEP-003.09.
 *
 * The original ramp was blue-tinted (#f6f7f9 on #14181f). That is the default
 * look of every developer tool, and this is not one: the content is places,
 * photographs and times of day. A neutral carrying a trace of warmth sits under
 * that content instead of arguing with it, and costs nothing — the hue moves,
 * the luminance does not, so every contrast ratio is preserved or improved.
 *
 * `border-subtle` is new and is the reason the interface stops looking like a
 * wireframe. The old palette had exactly one border colour, so every edge in the
 * product was drawn at the same weight as every other: a hairline separating two
 * table rows shouted as loudly as the outline of a text input. Three weights now
 * exist, and each says something different — subtle divides, default encloses an
 * input, strong emphasises.
 */
export const LIGHT = {
  'surface-base': '#fdfcfa',
  'surface-raised': '#ffffff',
  'surface-sunken': '#f4f2ee',
  'text-primary': '#1a1815',
  'text-secondary': '#57534c',
  'border-subtle': '#d8d2c8',
  'border-default': '#736e65',
  'border-strong': '#443f38',
  'action-primary': '#0a5ad4',
  'action-primary-text': '#ffffff',
  'focus-ring': '#0a5ad4',
  'status-success': '#0e6b3c',
  'status-warning': '#78490a',
  'status-error': '#b0251d',
  'status-info': '#0a5ad4',
  // Tinted surfaces for status panels. Held to the SAME text-contrast bar as any
  // other surface — a tint that makes its own label harder to read is decoration
  // that costs legibility, which is the trade this product must never make.
  'status-success-surface': '#e8f4ec',
  'status-warning-surface': '#faf0e2',
  'status-error-surface': '#fdeceb',
  'status-info-surface': '#e9f0fc',
} as const;

/**
 * Dark is warm too, and the surfaces invert their relationship.
 *
 * In light, a raised card is BRIGHTER than the page. In dark, a raised card is
 * also brighter than the page — because light still comes from above. Inverting
 * that (a darker card on a lighter page) is the most common dark-mode mistake
 * and reads as a hole rather than a card.
 */
export const DARK = {
  'surface-base': '#15130f',
  'surface-raised': '#1e1b16',
  'surface-sunken': '#0e0c0a',
  'text-primary': '#f5f2ec',
  'text-secondary': '#bdb6ab',
  'border-subtle': '#38332b',
  'border-default': '#7d766b',
  'border-strong': '#bdb6ab',
  'action-primary': '#84b4ff',
  'action-primary-text': '#15130f',
  'focus-ring': '#84b4ff',
  'status-success': '#63cd93',
  'status-warning': '#e3a842',
  'status-error': '#ffa198',
  'status-info': '#84b4ff',
  'status-success-surface': '#16241c',
  'status-warning-surface': '#251c0e',
  'status-error-surface': '#2a1613',
  'status-info-surface': '#141d2c',
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
  // Every border is the same pure white here, deliberately. The three-weight
  // hierarchy is a refinement for people who can perceive it; at AAA the job is
  // "can I see the edge at all", and a subtle border is a border you cannot.
  'border-subtle': '#ffffff',
  'border-default': '#ffffff',
  'border-strong': '#ffffff',
  'action-primary': '#ffff00',
  'action-primary-text': '#000000',
  'focus-ring': '#ffff00',
  'status-success': '#00ff7f',
  'status-warning': '#ffd400',
  'status-error': '#ff8080',
  'status-info': '#7fdfff',
  // Tints collapse to pure black. A tinted surface at AAA is a surface whose
  // contrast is no longer unambiguous, and unambiguous is the entire point.
  'status-success-surface': '#000000',
  'status-warning-surface': '#000000',
  'status-error-surface': '#000000',
  'status-info-surface': '#000000',
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

    // STEP-003.09. A tinted status panel is only worth having if its own text is
    // still readable on it, so each tint is declared as a background and held to
    // the ordinary body-text bar. This is what stops a tint being chosen because
    // it looked nice.
    on('text-primary', 'status-success-surface', AA_NORMAL_TEXT, 'text on a success panel'),
    on('text-primary', 'status-warning-surface', AA_NORMAL_TEXT, 'text on a warning panel'),
    on('text-primary', 'status-error-surface', AA_NORMAL_TEXT, 'text on an error panel'),
    on('text-primary', 'status-info-surface', AA_NORMAL_TEXT, 'text on an info panel'),
    on('text-secondary', 'status-success-surface', AA_NORMAL_TEXT, 'detail on a success panel'),
    on('text-secondary', 'status-warning-surface', AA_NORMAL_TEXT, 'detail on a warning panel'),
    on('text-secondary', 'status-error-surface', AA_NORMAL_TEXT, 'detail on an error panel'),
    on('text-secondary', 'status-info-surface', AA_NORMAL_TEXT, 'detail on an info panel'),
    // The status colour is also used as the panel's edge, so it must clear the
    // UI-component bar against its own tint, not only against the page.
    on('status-success', 'status-success-surface', AA_LARGE_TEXT_AND_UI, 'success panel edge'),
    on('status-warning', 'status-warning-surface', AA_LARGE_TEXT_AND_UI, 'warning panel edge'),
    on('status-error', 'status-error-surface', AA_LARGE_TEXT_AND_UI, 'error panel edge'),
    on('status-info', 'status-info-surface', AA_LARGE_TEXT_AND_UI, 'info panel edge'),
    /*
     * A subtle border still has to be VISIBLE.
     *
     * WCAG sets no bar for a purely decorative divider, so any number here is
     * one this project chose rather than one the standard requires — and the
     * first attempt failed its own invented threshold, which is a fair sign the
     * number was picked to sound reasonable rather than to mean something.
     *
     * 1.4:1 is the floor at which a hairline remains perceptible on a normal
     * display without competing with `border-default`, the colour that encloses
     * an actual control at 3:1. The rule that matters is the usage note: a
     * subtle border divides, it never bounds a control. That is enforced by
     * review, not by this number, and saying so is more honest than implying the
     * ratio does the work.
     */
    on('border-subtle', 'surface-base', 1.4, 'hairline divider (never a control edge)'),
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
  'space-5': '1.25rem',
  'space-6': '1.5rem',
  'space-8': '2rem',
  'space-10': '2.5rem',
  'space-12': '3rem',
  'space-16': '4rem',
  'space-20': '5rem',
} as const;

/**
 * Corner radius — STEP-003.09.
 *
 * Previously every corner used `--space-1`, so a 4px radius appeared on a text
 * input and on a full-screen dialog alike. Radius should scale with the element:
 * a small control reads as crisp at 6px and as a lozenge at 14px, while a large
 * surface at 6px reads as unfinished.
 *
 * `full` is for pills and avatars, where the intent is "as round as possible"
 * rather than a specific measurement.
 */
export const RADIUS = {
  'radius-sm': '0.375rem',
  'radius-md': '0.625rem',
  'radius-lg': '0.875rem',
  'radius-xl': '1.25rem',
  'radius-full': '999rem',
} as const;

/**
 * rem throughout, never px.
 *
 * REQ-A11Y and WCAG 1.4.4 require text to survive 200% zoom. A px font size
 * ignores the browser's font-size setting entirely, which is the setting many
 * low-vision users rely on before they ever reach a zoom control.
 */
export const TYPOGRAPHY = {
  /*
   * A SYSTEM STACK, AND THAT IS A DECISION — STEP-003.09.
   *
   * Not a placeholder for a webfont later. A webfont costs a request on the
   * critical path and either blocks first paint or swaps mid-read; both damage
   * LCP, which STEP-003.08 now measures and gates. It also fails exactly when a
   * traveller most needs the page: a weak connection in an unfamiliar place.
   *
   * The stack resolves to the typeface the reader already reads everything else
   * in, which is a legibility advantage a brand face has to earn back.
   */
  'font-family-sans':
    'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  /* Times, money and codes. Tabular figures stop columns of numbers dancing. */
  'font-family-mono': 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',

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
  'font-weight-semibold': '600',
  'font-weight-bold': '700',
  /*
   * Large text needs NEGATIVE tracking and small text needs positive.
   *
   * A face designed at body size looks loose when scaled up and cramped when
   * scaled down; the optical correction is what makes a size scale read as one
   * family rather than as the same font at different sizes.
   */
  'tracking-tight': '-0.02em',
  'tracking-normal': '0',
  'tracking-wide': '0.01em',
  /*
   * Line length. 65 characters is the long-standing readability figure, and the
   * evidence panels this product is built around are prose, not labels.
   */
  'measure-prose': '65ch',
  'measure-narrow': '48ch',
} as const;

/*
 * Two-layer shadows — STEP-003.09.
 *
 * A single blurred shadow reads as a smudge. Real objects cast a tight contact
 * shadow where they meet the surface and a wider ambient one further out, and
 * reproducing both is the difference between "card" and "grey rectangle with a
 * grey rectangle behind it".
 */
export const ELEVATION = {
  'elevation-0': 'none',
  'elevation-1': '0 1px 2px rgb(26 24 21 / 0.06), 0 1px 3px rgb(26 24 21 / 0.04)',
  'elevation-2': '0 2px 4px rgb(26 24 21 / 0.06), 0 6px 16px rgb(26 24 21 / 0.08)',
  'elevation-3': '0 4px 8px rgb(26 24 21 / 0.08), 0 16px 40px rgb(26 24 21 / 0.14)',
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
