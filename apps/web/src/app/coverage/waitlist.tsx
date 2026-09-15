'use client';

import { Checkbox, Notification, NotificationRegion, TextInput } from '@journeylab/ui';
import { useState } from 'react';

/**
 * "Tell me when you can plan this" — STEP-007.04 (REQ-TRIP-002, REQ-PRIV-002,
 * REQ-PRIV-004).
 *
 * WHAT THIS SURFACE IS FOR
 *   The person reading it has just been told no. Everything here is shaped by that:
 *   it asks for the least it can, it says what will happen with what it asks for,
 *   and it hands back the means to undo it in the same breath.
 *
 * THE CONSENT BOX IS NEVER PRE-TICKED, AND THE STATE PROVES IT
 *   `useState(false)`. Not a prop with a default, not a `defaultChecked`, not a
 *   value the server can seed — the component cannot render a ticked box on first
 *   paint because there is no code path that produces one. A pre-ticked consent is
 *   not consent under `REQ-PRIV-002`, and the usual way it appears is not malice
 *   but a default written for convenience somewhere far from the checkbox.
 *
 * THE SUBMIT BUTTON IS NOT DISABLED WHEN CONSENT IS MISSING
 *   A disabled control tells a keyboard or screen-reader user nothing about WHY it
 *   is disabled, and a disabled button is skipped in the tab order on some
 *   platforms — so the person is left with a form that appears broken. Pressing it
 *   without consent produces a sentence that says what is missing. `REQ-A11Y-001`.
 *
 * THE TOKEN IS SHOWN ONCE, AND THE PAGE SAYS SO
 *   The server stores only its hash and cannot re-issue it. A component that
 *   quietly kept the token in memory and offered a friendly "unsubscribe" button
 *   would be the one place it survives — and it would survive exactly as long as
 *   the tab stays open, which is not a property anybody could reason about. So it
 *   is displayed, its one-time nature is stated, and withdrawal takes it as input
 *   like any other credential.
 */

interface JoinedState {
  readonly purpose: string;
  readonly granted_at: string;
  readonly withdrawal_token: string;
}

type Outcome =
  | { readonly kind: 'idle' }
  | { readonly kind: 'sending' }
  | { readonly kind: 'joined'; readonly joined: JoinedState }
  | { readonly kind: 'refused'; readonly detail: string }
  | { readonly kind: 'unreachable' };

type Withdrawal =
  | { readonly kind: 'idle' }
  | { readonly kind: 'sending' }
  | { readonly kind: 'withdrawn' }
  | { readonly kind: 'rejected' }
  | { readonly kind: 'unreachable' };

const API_BASE = process.env.NEXT_PUBLIC_JOURNEYLAB_API_URL ?? 'http://127.0.0.1:5710';

/**
 * One key per user intent, regenerated per submission attempt.
 *
 * `crypto.randomUUID` needs a secure context, which a page served over plain HTTP
 * on a developer machine is not. The fallback is not a security control — the key
 * is a de-duplication token, not a secret — so a weaker source is correct here and
 * would not be for the withdrawal token, which is minted on the server.
 */
function idempotencyKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `waitlist-${crypto.randomUUID()}`;
  }
  return `waitlist-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

export function Waitlist() {
  const [email, setEmail] = useState('');
  const [destination, setDestination] = useState('');
  // THE ONE LINE THIS COMPONENT IS ABOUT.
  const [consented, setConsented] = useState(false);
  const [formError, setFormError] = useState('');
  const [outcome, setOutcome] = useState<Outcome>({ kind: 'idle' });

  const [token, setToken] = useState('');
  const [withdrawal, setWithdrawal] = useState<Withdrawal>({ kind: 'idle' });

  async function onJoin(event: React.FormEvent) {
    event.preventDefault();

    if (!email.trim()) {
      setFormError('Enter an email address so we have somewhere to send it.');
      return;
    }
    if (!consented) {
      // Checked here as well as on the server. Not a duplicated rule — the server
      // is what refuses, and this exists so the answer is immediate rather than a
      // round trip to be told about a box on the screen in front of them.
      setFormError('Tick the box to tell us we may contact you about this one thing.');
      return;
    }
    setFormError('');
    setOutcome({ kind: 'sending' });

    try {
      const response = await fetch(`${API_BASE}/waitlist`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          accept: 'application/json',
          'Idempotency-Key': idempotencyKey(),
        },
        body: JSON.stringify({
          email: email.trim(),
          region_query: destination.trim() || undefined,
          consent: { purpose: 'waitlist_notification', granted: true },
        }),
      });
      const body = await response.json();
      if (response.ok) {
        setOutcome({ kind: 'joined', joined: body as JoinedState });
        // Cleared on success. Keeping the address in a controlled input after it
        // has been sent leaves it in the DOM, in a form restore and in a password
        // manager's heuristics, for no benefit.
        setEmail('');
        setConsented(false);
      } else {
        setOutcome({
          kind: 'refused',
          detail: typeof body.detail === 'string' ? body.detail : 'That could not be recorded.',
        });
      }
    } catch {
      // Not surfaced: the caught error carries a host and a port, and this string
      // is rendered to the public.
      setOutcome({ kind: 'unreachable' });
    }
  }

  async function onWithdraw(event: React.FormEvent) {
    event.preventDefault();
    if (!token.trim()) return;
    setWithdrawal({ kind: 'sending' });
    try {
      const response = await fetch(`${API_BASE}/waitlist:withdraw`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          accept: 'application/json',
          'Idempotency-Key': idempotencyKey(),
        },
        body: JSON.stringify({ withdrawal_token: token.trim() }),
      });
      if (response.ok) {
        setWithdrawal({ kind: 'withdrawn' });
        setToken('');
      } else {
        setWithdrawal({ kind: 'rejected' });
      }
    } catch {
      setWithdrawal({ kind: 'unreachable' });
    }
  }

  return (
    <section aria-labelledby="waitlist-heading">
      <h2 id="waitlist-heading">Tell me when this changes</h2>
      <p>
        If your destination is not here yet, we can let you know when it is. One message, about that
        one thing.
      </p>

      <form onSubmit={onJoin} noValidate>
        <TextInput
          label="Email address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.currentTarget.value)}
          description="Used only to send the message you are asking for. Nothing else is stored about you."
          required
          autoComplete="email"
        />

        <TextInput
          label="Which destination? (optional)"
          value={destination}
          onChange={(e) => setDestination(e.currentTarget.value)}
          description="So we know which place to tell you about. Free text — it is not on our list yet."
          maxLength={64}
        />

        <Checkbox
          label="You may email me when this destination becomes plannable."
          checked={consented}
          onChange={(e) => setConsented(e.currentTarget.checked)}
          description="This permission covers that message and nothing else. We delete your address once it is sent, or after 12 months if this destination has not opened by then. You can withdraw it at any time, and doing so deletes your address immediately."
        />

        {formError ? <p role="alert">{formError}</p> : null}

        <button type="submit" className="jl-button" disabled={outcome.kind === 'sending'}>
          {outcome.kind === 'sending' ? 'Adding…' : 'Add me to the list'}
        </button>
      </form>

      <NotificationRegion
        polite={
          outcome.kind === 'joined' ? (
            <Notification politeness="polite" title="You are on the list">
              <p>
                We will email you once about this destination, and then not again unless you ask.
              </p>
              <p>
                <strong>Save this withdrawal code.</strong> It is shown once and we cannot show it
                again — it is the only way to remove yourself, and we deliberately do not store a
                copy we could look up.
              </p>
              <p>
                <code data-withdrawal-token>{outcome.joined.withdrawal_token}</code>
              </p>
            </Notification>
          ) : null
        }
        assertive={
          outcome.kind === 'refused' ? (
            <Notification politeness="assertive" title="That could not be recorded">
              <p>{outcome.detail}</p>
            </Notification>
          ) : outcome.kind === 'unreachable' ? (
            <Notification politeness="assertive" title="We could not reach the waitlist">
              <p>
                Nothing has been stored. This is a problem on our side — please try again shortly.
              </p>
            </Notification>
          ) : null
        }
      />

      <h3>Remove yourself</h3>
      <p>
        Paste the withdrawal code you were given. This deletes your address and cancels the
        permission; it affects nothing else.
      </p>
      <form onSubmit={onWithdraw} noValidate>
        <TextInput
          label="Withdrawal code"
          value={token}
          onChange={(e) => setToken(e.currentTarget.value)}
          autoComplete="off"
        />
        <button type="submit" className="jl-button" disabled={withdrawal.kind === 'sending'}>
          {withdrawal.kind === 'sending' ? 'Removing…' : 'Remove me and delete my address'}
        </button>
      </form>

      <NotificationRegion
        polite={
          withdrawal.kind === 'withdrawn' ? (
            <Notification politeness="polite" title="Removed">
              <p>
                Your address has been deleted. We keep a dated note that a permission was given and
                withdrawn, with nothing in it that identifies you — that record is what shows we
                held your address lawfully while we had it.
              </p>
            </Notification>
          ) : null
        }
        assertive={
          withdrawal.kind === 'rejected' ? (
            <Notification politeness="assertive" title="That code does not work">
              <p>
                We cannot tell you whether it was never valid or has already been used — answering
                that would let somebody test codes until one worked.
              </p>
            </Notification>
          ) : withdrawal.kind === 'unreachable' ? (
            <Notification politeness="assertive" title="We could not reach the waitlist">
              <p>Nothing has changed. Please try again shortly.</p>
            </Notification>
          ) : null
        }
      />
    </section>
  );
}

/**
 * What there is to say about a place we cannot plan — STEP-007.04.
 *
 * THE RISK THE SUB-STEP NAMED, AND HOW THIS ANSWERS IT
 *   §4 of the sub-step: *"Showing a beautiful page for a place we cannot plan may
 *   read as a promise."* That is the whole design constraint. Photography and
 *   curated highlights would look better and would imply a depth of knowledge we do
 *   not have — we have no provider data for these regions at all (`ENH-007`), so
 *   anything specific here would be written from memory and presented as research.
 *
 *   So: text, no imagery, no named places, and the limitation stated first rather
 *   than in a footnote. It tells the traveller what JourneyLab would need before it
 *   could help, which is honest and is also the only thing we actually know.
 */
export function Inspiration() {
  return (
    <section aria-labelledby="inspiration-heading">
      <h2 id="inspiration-heading">Somewhere we cannot plan yet</h2>

      {/* The limitation FIRST. A caveat after the encouragement is a caveat that
          has already been skipped. */}
      <p>
        <strong>JourneyLab cannot plan a trip here yet, and this is not a preview of one.</strong>{' '}
        We only add a region once we can answer questions about it from sources we can cite —
        transit that actually runs on the day you travel, opening hours that are current, and
        weather we can attribute. Until then we would be guessing, and a confident guess is worse
        than an honest gap.
      </p>

      <h3>What we would need before this region appears</h3>
      <ul>
        <li>
          Transit schedules we can pin to a version, so a plan does not quietly change underneath
          you.
        </li>
        <li>
          Opening hours and accessibility information with a date attached, so you can see how old
          the answer is.
        </li>
        <li>A weather source we are licensed to use and can name as the origin of a forecast.</li>
      </ul>

      <p>
        If you are travelling here sooner than that, use a local guide or the operator&rsquo;s own
        timetable. We would rather point you somewhere useful than keep you here.
      </p>
    </section>
  );
}
