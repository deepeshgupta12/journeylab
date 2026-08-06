/**
 * WCAG 2.2 contrast maths — STEP-003.01 (REQ-A11Y-004).
 *
 * WHY COMPUTE THIS RATHER THAN ASSERT IT
 *   "These colours pass AA" is a claim someone checked once, in a tool, against
 *   values that have since been edited. Computing the ratio from the token values
 *   themselves means the claim is re-verified on every test run, and editing a
 *   colour to something that fails breaks the build rather than shipping.
 *
 * The algorithm is WCAG 2.x relative luminance:
 *   https://www.w3.org/TR/WCAG22/#dfn-relative-luminance
 *   https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio
 */

/** Minimum contrast for body text at AA. */
export const AA_NORMAL_TEXT = 4.5;

/**
 * Minimum for large text (>=18.66px bold or >=24px) AND for non-text UI
 * components and graphical objects — WCAG 2.2 SC 1.4.11. Borders, focus rings and
 * icons are held to this, not to 4.5.
 */
export const AA_LARGE_TEXT_AND_UI = 3;

/** AAA body text. The high-contrast token set is held to this. */
export const AAA_NORMAL_TEXT = 7;

export interface Rgb {
  readonly r: number;
  readonly g: number;
  readonly b: number;
}

export function parseHex(hex: string): Rgb {
  const value = hex.trim().replace(/^#/, '');
  const expanded =
    value.length === 3
      ? value
          .split('')
          .map((c) => c + c)
          .join('')
      : value;

  if (!/^[0-9a-fA-F]{6}$/.test(expanded)) {
    // Throwing rather than returning black: a silently-black colour would make a
    // contrast test PASS against a white background, hiding the malformed token.
    throw new Error(`not a valid hex colour: ${hex}`);
  }
  return {
    r: Number.parseInt(expanded.slice(0, 2), 16),
    g: Number.parseInt(expanded.slice(2, 4), 16),
    b: Number.parseInt(expanded.slice(4, 6), 16),
  };
}

/** Linearise one 0-255 channel, per WCAG. */
function channelLuminance(value: number): number {
  const c = value / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

export function relativeLuminance(color: Rgb): number {
  return (
    0.2126 * channelLuminance(color.r) +
    0.7152 * channelLuminance(color.g) +
    0.0722 * channelLuminance(color.b)
  );
}

/**
 * Contrast ratio between two colours, 1:1 to 21:1.
 *
 * Order-independent by construction — the lighter colour is always the numerator,
 * so a caller cannot get a different answer by passing foreground and background
 * the other way round.
 */
export function contrastRatio(a: string, b: string): number {
  const first = relativeLuminance(parseHex(a));
  const second = relativeLuminance(parseHex(b));
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

export function meetsContrast(foreground: string, background: string, minimum: number): boolean {
  return contrastRatio(foreground, background) >= minimum;
}
