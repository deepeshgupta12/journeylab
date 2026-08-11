---
owner: Deepesh Kumar Gupta
requirement_ids: [REQ-A11Y-001, REQ-A11Y-002, REQ-A11Y-003, REQ-A11Y-004, REQ-A11Y-005, REQ-A11Y-006]
created: 2026-08-10
sub_step: STEP-003.08
---

# What the accessibility automation cannot catch

`STEP-003.08` §5 asks for this document by name: *"Document what automation
cannot catch, so it is not mistaken for full coverage."*

This is not a disclaimer. It is the list that keeps the manual work scheduled
rather than quietly dropped once the pipeline is green.

---

## 1. The honest number

Automated rules detect somewhere between **a third and a half** of the WCAG
failures a real audit finds. That figure is consistent across published studies
of axe-family tooling, and it is not a criticism of axe — most of the remaining
criteria are about *meaning*, and a machine has no access to meaning.

**A green run means no violation of the rules a machine can express. It does not
mean the product is usable.**

---

## 2. What is now automated

| Check | Where | Runs on |
| --- | --- | --- |
| axe, WCAG 2.2 A + AA | `apps/web/src/test/a11y.spec.ts` | Shell, gallery, gallery in RTL, dialog open, drawer open |
| Skip link focusable **and visible on focus** | same | Real layout box, not just presence |
| Focus trap: absent everywhere, present in dialogs | same | 400-tab traversal + dialog containment |
| Visible focus indicator on every control | same | Computed outline / shadow / underline |
| Touch targets ≥ 24×24 (SC 2.5.8), nav ≥ 44×44 | same | Pixel 7 viewport |
| No horizontal scroll at 320px (SC 1.4.10) | same | Measured overflow |
| The 48rem breakpoint behaves | same | Both sides of it |
| forced-colors rendering | same | Chromium forced-colors emulation |
| RTL layout and mirrored logical properties | same | `?dir=rtl` |
| LCP ≤ 2.5 s, CLS ≤ 0.1, interaction ≤ 200 ms | same | Chromium, production build |
| Contrast ratios for every declared token pairing | `packages/ui/src/tokens.test.ts` | Computed, not eyeballed |
| Component semantics, roles, names, live regions | 267 jsdom tests | Every primitive, every state |
| Physical CSS properties (RTL readiness) | `tests/guards/logical-css.sh` | Every stylesheet, every commit |

---

## 3. What is NOT automated, and never will be

### 3.1 Whether the announcement makes sense

axe checks that a live region exists and that a control has an accessible name.
It cannot tell you that the name is *"Button"*, that the announcement is
*"Update complete"* when three of five scenarios failed, or that a table caption
says *"Table 2"*.

**Only a person listening can.** This is the single largest gap.

### 3.2 Screen-reader behaviour

Every screen reader implements the specifications differently, and the
differences are not bugs — they are decades of divergent convention. A pattern
that is announced perfectly by NVDA in Firefox can be silent in VoiceOver in
Safari. No headless browser reproduces any of them.

Required combinations for a release audit:

| Screen reader | Browser | Platform |
| --- | --- | --- |
| NVDA | Firefox | Windows |
| JAWS | Chrome | Windows |
| VoiceOver | Safari | macOS |
| VoiceOver | Safari | iOS |
| TalkBack | Chrome | Android |

### 3.3 Focus order that is *logical*

The traversal test proves focus never gets stuck and always returns to the
start. It cannot prove the order is sensible — a form that tabs label, submit,
first field, second field passes every automated check and is unusable.

### 3.4 Cognitive load, reading level and error recovery

`REQ-A11Y-001` is about people completing tasks. Whether the infeasibility
explanation can be acted on, whether the conflict set is comprehensible, whether
someone under time pressure in an airport can recover from a mistake — none of
this has a rule.

### 3.5 Meaning conveyed by colour

`REQ-A11Y-004` is partially automated: the token contrast tests and the
forced-colors run catch the crude failures. What they cannot catch is a chart
where two series are distinguishable only by hue, or a status that technically
has an icon which happens to be identical across three states.

### 3.6 Core Web Vitals in the field — and in CI

The measurements in `a11y.spec.ts` are **lab numbers**: one machine, over
loopback, no network. `FRONTEND_ARCHITECTURE` §7 specifies mid-tier mobile on
4G. The lab run catches regressions; it cannot confirm the budget is met for a
traveller on a ferry. Field measurement needs real-user monitoring, which is
`STEP-024`.

**A second limit surfaced when the suite first ran in a container.** LCP measured
**10,760 ms** there against ~200 ms on the development machine — a 4 GB container
running a browser per worker, not a slow page. So the two kinds of metric are now
treated differently:

| Metric | Enforced in CI | Why |
| --- | --- | --- |
| **CLS** | **Yes** | A ratio of movement to viewport. A page that shifts on a slow machine shifts on a fast one, so the number means the same thing everywhere |
| LCP | No — measured and reported | A duration. On a contended runner it describes the runner |
| Interaction latency | Relaxed to 1 s | Same. The 200 ms product budget is enforced locally, where the measurement means something |

Enforcing a duration against a machine whose speed is not controlled produces a
flaky gate, and `BUG-016` already established that a flaky gate is worse than a
failing one — it teaches people that re-running is the fix.

**None of this makes the budgets met.** They are unmet, owned by `STEP-024`, and
listed in §4.

### 3.7 Zoom, reflow and text spacing beyond the tested points

Two viewports are tested. WCAG 1.4.4 (200% zoom), 1.4.10 (reflow at 320 CSS px
at 400% zoom) and 1.4.12 (text spacing overrides) cover a continuum.

### 3.8 Assistive technology that is not a screen reader

Voice control (Dragon, Voice Control), switch access, screen magnifiers, and
braille displays all have distinct failure modes. Voice control in particular
breaks when the visible label and the accessible name disagree — a mismatch that
passes axe cleanly.

---

## 4. What must therefore be scheduled

| Activity | Cadence | Owner step |
| --- | --- | --- |
| Manual screen-reader journeys over the golden paths | **Every release** | STEP-003.08 defines; each feature step executes |
| Keyboard-only completion of every MVP task | Every release | — |
| Voice-control pass on primary flows | Before GA | — |
| Zoom to 200% and 400% on core routes | Before GA | — |
| Independent audit by a practitioner who uses AT daily | Before GA | — |
| Real-user CWV monitoring | Continuous, once built | STEP-024 |

`FRONTEND_ARCHITECTURE` §8 already commits to "automated axe checks in CI **+
manual screen-reader journeys**". This document is what stops the second half of
that sentence being forgotten because the first half is green.

---

## 5. How to read a green pipeline

> The accessibility gate passed. That means we did not ship any of the defects a
> machine can name. It says nothing about whether a person using a screen reader
> can plan a trip.

Anyone claiming `REQ-A11Y-001` is met on the strength of CI alone is
over-claiming, and this document exists to be pointed at when they do.
