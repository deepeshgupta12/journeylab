'use client';

/**
 * The component gallery — STEP-003.08.
 *
 * Every primitive STEP-003.01–.07 produced, in every quality state, on one page.
 *
 * WHY THIS IS THE ACCESSIBILITY SURFACE
 *   `a11y.spec.ts` walks this page in a real browser: axe over the whole
 *   document, a keyboard traversal that must not get stuck, touch-target
 *   measurement at a phone viewport, forced-colors, and RTL. jsdom cannot do any
 *   of those — it has no layout, no paint and no forced-colors mode, so seven
 *   sub-steps' worth of components had never been measured, only asserted about.
 *
 * WHY EVERY STATE, NOT A HAPPY PATH
 *   `FRONTEND_ARCHITECTURE` §8: "all quality states". A gallery of components in
 *   their success state proves the least interesting thing about them. The error,
 *   stale, infeasible, offline and unauthorized panels are where the copy is
 *   longest, the contrast is riskiest and the semantics are easiest to get wrong.
 *
 * Interactive state lives here because a dialog that cannot be opened is not a
 * dialog under test. The server component is the gate and the page frame.
 */

import {
  Checkbox,
  DataList,
  DataTable,
  DateInput,
  Dialog,
  EmptyState,
  FeatureErrorBoundary,
  formatMoney,
  InfeasibleState,
  MobileNavigation,
  money,
  type NavItem,
  Navigation,
  Notification,
  NotificationRegion,
  NumberInput,
  OfflineState,
  PartialDataState,
  Progress,
  ProviderDownState,
  RadioGroup,
  Select,
  Skeleton,
  SolverTimeoutState,
  StaleDataState,
  type TableColumn,
  TextInput,
  UnauthorizedState,
} from '@journeylab/ui';
import { useState } from 'react';

interface Leg {
  id: string;
  day: string;
  from: string;
  to: string;
  minutes: number;
}

const LEGS: Leg[] = [
  { id: '1', day: 'Mon', from: 'Naxos', to: 'Paros', minutes: 45 },
  { id: '2', day: 'Tue', from: 'Paros', to: 'Antiparos', minutes: 20 },
  { id: '3', day: 'Wed', from: 'Antiparos', to: 'Sifnos', minutes: 95 },
];

const COLUMNS: TableColumn<Leg>[] = [
  { key: 'day', header: 'Day', cell: (r) => r.day, sortable: true },
  { key: 'from', header: 'From', cell: (r) => r.from, sortable: true },
  { key: 'to', header: 'To', cell: (r) => r.to },
  {
    key: 'minutes',
    header: 'Duration',
    cell: (r) => `${r.minutes} min`,
    value: (r) => r.minutes,
    sortable: true,
  },
];

const NAV_ITEMS: NavItem[] = [
  { href: '/trips', label: 'Trips', operation: 'read_trip' },
  { href: '/trips/new', label: 'New trip', operation: 'create_trip' },
];

function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section aria-labelledby={`${id}-heading`} className="jl-gallery__section">
      <h2 id={`${id}-heading`}>{title}</h2>
      <div className="jl-gallery__grid">{children}</div>
    </section>
  );
}

function Specimen({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <figure className="jl-gallery__specimen">
      {/*
        A figcaption, not a div. Each specimen is a labelled figure so a screen
        reader user walking the gallery can tell which state they are in — the
        same reason the table needs a caption rather than a heading beside it.
      */}
      <figcaption className="jl-gallery__caption">{label}</figcaption>
      <div className="jl-gallery__stage">{children}</div>
    </figure>
  );
}

function Boom(): never {
  throw new Error('gallery: deliberate failure to render the contained-error state');
}

export function Gallery() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [text, setText] = useState('Naxos');
  const [amount, setAmount] = useState('1,250');
  const [choice, setChoice] = useState('ferry');
  const [departure, setDeparture] = useState('2026-03-28');
  const [checked, setChecked] = useState(true);
  const [notices, setNotices] = useState<string[]>(['Scenario B recalculated.']);

  return (
    <>
      <Section id="nav" title="Navigation">
        <Specimen label="Desktop, role: trip_owner">
          <Navigation items={NAV_ITEMS} actorRole="trip_owner" currentPath="/trips" />
        </Specimen>
        <Specimen label="Desktop, role: guest — fewer items, and that is presentation only">
          <Navigation items={NAV_ITEMS} actorRole="guest" currentPath="/trips" />
        </Specimen>
        <Specimen label="Mobile drawer — the toggle appears below 48rem only">
          <MobileNavigation
            items={NAV_ITEMS}
            actorRole="trip_owner"
            currentPath="/trips"
            open={drawerOpen}
            onOpen={() => setDrawerOpen(true)}
            onClose={() => setDrawerOpen(false)}
          />
        </Specimen>
      </Section>

      <Section id="form" title="Form primitives">
        <Specimen label="Text input">
          <TextInput
            label="Destination"
            description="Where the trip starts."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </Specimen>
        <Specimen label="Text input — required and in error">
          <TextInput
            label="Traveller name"
            required
            error="Enter the name exactly as it appears on the passport."
            defaultValue=""
          />
        </Specimen>
        <Specimen label="Text input — disabled">
          <TextInput label="Trip code" disabled defaultValue="JL-2026-0007" />
        </Specimen>
        <Specimen label="Number input — locale-aware">
          <NumberInput
            label="Budget"
            locale="en-GB"
            description="Grouping separators are accepted."
            value={amount}
            onValueChange={(raw) => setAmount(raw)}
          />
        </Specimen>
        <Specimen label="Date input — a calendar date, never an instant">
          <DateInput
            label="Departure"
            description="Interpreted in the trip's time zone, not the browser's."
            value={departure}
            onDateChange={(raw) => setDeparture(raw)}
          />
        </Specimen>
        <Specimen label="Date input — impossible date rejected">
          <DateInput
            label="Return"
            error="2026-02-30 is not a date. Enter a real one."
            value="2026-02-30"
            onDateChange={() => undefined}
          />
        </Specimen>
        <Specimen label="Select">
          <Select
            label="Cabin"
            options={[
              { value: 'deck', label: 'Deck' },
              { value: 'seat', label: 'Reserved seat' },
              { value: 'cabin', label: 'Cabin' },
            ]}
            defaultValue="seat"
          />
        </Specimen>
        <Specimen label="Radio group">
          <RadioGroup
            label="Mode"
            name="gallery-mode"
            options={[
              { value: 'ferry', label: 'Ferry' },
              { value: 'flight', label: 'Flight' },
              { value: 'road', label: 'Road' },
            ]}
            value={choice}
            onValueChange={setChoice}
          />
        </Specimen>
        <Specimen label="Checkbox">
          <Checkbox
            label="Avoid overnight travel"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
          />
        </Specimen>
      </Section>

      <Section id="data" title="Table, list and export">
        <Specimen label="Table — sortable, with CSV export">
          <DataTable
            caption="Ferry legs"
            columns={COLUMNS}
            rows={LEGS}
            rowKey={(r) => r.id}
            csvFilename="legs.csv"
          />
        </Specimen>
        <Specimen label="Table — empty">
          <DataTable
            caption="Ferry legs (no results)"
            columns={COLUMNS}
            rows={[]}
            rowKey={(r) => r.id}
            emptyMessage="No legs match these constraints."
          />
        </Specimen>
        <Specimen label="List — the narrow-viewport equivalent">
          <DataList caption="Ferry legs" columns={COLUMNS} rows={LEGS} rowKey={(r) => r.id} />
        </Specimen>
      </Section>

      <Section id="states" title="Quality states">
        <Specimen label="Loading">
          <Skeleton label="Loading scenarios" />
        </Specimen>
        <Specimen label="Progress, cancellable">
          <Progress label="Optimising scenarios" percent={62} onCancel={() => undefined} />
        </Specimen>
        <Specimen label="Empty">
          <EmptyState action={<button type="button">Widen the dates</button>}>
            No scenarios yet.
          </EmptyState>
        </Specimen>
        <Specimen label="Partial data">
          <PartialDataState>Ferry times loaded; accommodation prices did not.</PartialDataState>
        </Specimen>
        <Specimen label="Stale data — an estimate is never shown as confirmed">
          <StaleDataState subject="Ferry timetable" observedAt={new Date('2026-08-08T06:00:00Z')}>
            Shown from the last successful fetch.
          </StaleDataState>
        </Specimen>
        <Specimen label="Provider down">
          <ProviderDownState>The timetable provider is not responding.</ProviderDownState>
        </Specimen>
        <Specimen label="Infeasible — a minimal conflict set, never a plausible invalid plan">
          <InfeasibleState
            conflicts={[
              'Arrive Sifnos before 18:00 on Wednesday',
              'Depart Antiparos after 16:30 on Wednesday',
              'Crossing takes 95 minutes',
            ]}
            relaxations={['Move the Sifnos arrival to 19:30', 'Depart Antiparos at 15:00']}
          />
        </Specimen>
        <Specimen label="Solver timeout">
          <SolverTimeoutState>Stopped after 30 seconds with no complete plan.</SolverTimeoutState>
        </Specimen>
        <Specimen label="Unauthorized">
          <UnauthorizedState>You do not have access to this trip.</UnauthorizedState>
        </Specimen>
        <Specimen label="Offline">
          <OfflineState>Showing the offline pack from 8 August.</OfflineState>
        </Specimen>
      </Section>

      <Section id="feedback" title="Dialog and notifications">
        <Specimen label="Dialog — focus trapped while open, restored on close">
          <button type="button" onClick={() => setDialogOpen(true)}>
            Open dialog
          </button>
          <Dialog
            open={dialogOpen}
            title="Discard this scenario?"
            onClose={() => setDialogOpen(false)}
            actions={
              <>
                <button type="button" onClick={() => setDialogOpen(false)}>
                  Discard
                </button>
                <button type="button" onClick={() => setDialogOpen(false)}>
                  Keep
                </button>
              </>
            }
          >
            Scenario B has unsaved edits. Discarding cannot be undone.
          </Dialog>
        </Specimen>
        <Specimen label="Notification — polite">
          <NotificationRegion
            polite={notices.map((n) => (
              <Notification
                key={n}
                politeness="polite"
                title="Scenario updated"
                onDismiss={() => setNotices([])}
              >
                {n}
              </Notification>
            ))}
          />
        </Specimen>
        <Specimen label="Notification — assertive">
          <Notification politeness="assertive" title="Connection lost">
            Retrying. Your edits are saved locally.
          </Notification>
        </Specimen>
      </Section>

      <Section id="errors" title="Error containment">
        <Specimen label="A failed feature must not remove its neighbours">
          <div>
            <p>Day 1: ferry to the island</p>
            <FeatureErrorBoundary feature="The map">
              <Boom />
            </FeatureErrorBoundary>
            <p>Day 2: coastal walk</p>
          </div>
        </Specimen>
      </Section>

      <Section id="money" title="Money and locale">
        <Specimen label="Minor units, formatted per locale and currency">
          <ul>
            <li>{formatMoney(money(125_000, 'EUR'), 'en-GB')} — EUR, en-GB</li>
            <li>{formatMoney(money(125_000, 'EUR'), 'de-DE')} — EUR, de-DE</li>
            <li>{formatMoney(money(18_500, 'JPY'), 'ja-JP')} — JPY has no minor unit</li>
            <li>{formatMoney(money(1_250, 'KWD'), 'en-GB')} — KWD has three</li>
          </ul>
        </Specimen>
      </Section>
    </>
  );
}
