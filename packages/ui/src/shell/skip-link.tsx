/**
 * Skip to content — STEP-003.05 (REQ-A11Y-001, WCAG 2.4.1).
 *
 * WHAT MAKES A SKIP LINK ACTUALLY WORK
 *   1. It must be the FIRST focusable element in the document. A skip link after
 *      the navigation skips nothing.
 *   2. It must be visible ON FOCUS. Permanently hidden with `display: none` or
 *      `visibility: hidden` removes it from the tab order entirely, so a keyboard
 *      user never reaches it — a "skip link" that cannot be focused is decoration.
 *   3. Its target must be focusable. Browsers vary on whether `href="#main"`
 *      moves focus or only scrolls; a `tabIndex={-1}` on the target makes it
 *      programmatically focusable so focus genuinely lands there.
 *
 * The visually-hidden technique used here (clip + 1px) keeps the element in the
 * accessibility tree and in the tab order while removing it from view.
 */

export interface SkipLinkProps {
  /** The id of the main landmark. Must carry tabIndex={-1} — see above. */
  readonly targetId: string;
  readonly children?: string;
}

export function SkipLink({ targetId, children = 'Skip to main content' }: SkipLinkProps) {
  return (
    <a href={`#${targetId}`} className="jl-skip-link" data-skip-link="">
      {children}
    </a>
  );
}
