'use client';

/**
 * Accessible data table — STEP-003.04 (REQ-A11Y-002).
 *
 * BUILT BEFORE ANY CHART, DELIBERATELY
 *   `REQ-A11Y-003` says no core action may require the map, and `REQ-A11Y-002`
 *   makes a table plus CSV the equal of every visualization. Building the
 *   non-visual path first makes that a foundation; retrofitting it after the
 *   charts exist makes it a second-class translation of decisions already taken
 *   for visual reasons.
 *
 * VIRTUALISATION AND ASSISTIVE TECHNOLOGY
 *   Rendering a window of 20 rows out of 10,000 is how a table stays fast, and it
 *   is also how a screen reader comes to announce "row 3 of 20". The user is told
 *   the dataset is 500 times smaller than it is, and there is no way for them to
 *   discover otherwise.
 *
 *   `aria-rowcount` on the grid and `aria-rowindex` on each row carry the TRUE
 *   totals independently of what is in the DOM. They are the entire reason
 *   virtualisation is safe here, and the sub-step names this as the thing to
 *   verify early: "virtualisation libraries frequently break AT row counts."
 */

import { useCallback, useId, useMemo, useState } from 'react';

import { type CsvColumn, downloadCsv, toCsv } from './csv';

export type SortDirection = 'ascending' | 'descending';

export interface TableColumn<Row> {
  readonly key: string;
  readonly header: string;
  /** Rendered value. */
  readonly cell: (row: Row) => React.ReactNode;
  /** Value used for sorting and CSV. Falls back to the rendered cell when omitted. */
  readonly value?: (row: Row) => string | number;
  readonly sortable?: boolean;
}

export interface DataTableProps<Row> {
  /**
   * A caption, not a heading above the table.
   *
   * A `<caption>` is announced when a screen reader enters the table; an `<h2>`
   * nearby is not. It is required because an unlabelled table in a page of
   * several is unidentifiable when navigating by table.
   */
  readonly caption: string;
  readonly columns: readonly TableColumn<Row>[];
  readonly rows: readonly Row[];
  readonly rowKey: (row: Row) => string;
  /** Window of rows to render. Omit to render all. */
  readonly virtualWindow?: { readonly start: number; readonly count: number };
  readonly csvFilename?: string;
  readonly emptyMessage?: string;
}

function defaultValue<Row>(column: TableColumn<Row>, row: Row): string | number {
  if (column.value) return column.value(row);
  const rendered = column.cell(row);
  return typeof rendered === 'string' || typeof rendered === 'number' ? rendered : '';
}

export function DataTable<Row>({
  caption,
  columns,
  rows,
  rowKey,
  virtualWindow,
  csvFilename,
  emptyMessage = 'No rows',
}: DataTableProps<Row>) {
  const [sort, setSort] = useState<{ key: string; direction: SortDirection } | null>(null);
  const captionId = useId();

  const sorted = useMemo(() => {
    if (!sort) return rows;
    const column = columns.find((c) => c.key === sort.key);
    if (!column) return rows;
    const factor = sort.direction === 'ascending' ? 1 : -1;
    return [...rows].sort((a, b) => {
      const left = defaultValue(column, a);
      const right = defaultValue(column, b);
      if (left === right) return 0;
      return (left < right ? -1 : 1) * factor;
    });
  }, [rows, columns, sort]);

  // The window is a rendering concern only. Every ARIA count below is computed
  // from the FULL set, never from what happens to be mounted.
  const visible = virtualWindow
    ? sorted.slice(virtualWindow.start, virtualWindow.start + virtualWindow.count)
    : sorted;
  const firstVisibleIndex = virtualWindow ? virtualWindow.start : 0;

  const toggleSort = useCallback((key: string) => {
    setSort((current) =>
      current?.key === key
        ? { key, direction: current.direction === 'ascending' ? 'descending' : 'ascending' }
        : { key, direction: 'ascending' },
    );
  }, []);

  const exportCsv = useCallback(() => {
    const csvColumns: CsvColumn<Row>[] = columns.map((column) => ({
      key: column.key,
      header: column.header,
      // CSV exports the FULL sorted set, not the rendered window. Exporting only
      // what is on screen would silently hand the user a truncated file.
      value: (row: Row) => defaultValue(column, row),
    }));
    downloadCsv(csvFilename ?? caption, toCsv(sorted, csvColumns));
  }, [columns, sorted, csvFilename, caption]);

  return (
    <div className="jl-table">
      {/*
       * THE SCROLL REGION IS FOCUSABLE, AND IT WRAPS ONLY THE TABLE — BUG-033.
       *
       * A container with `overflow-x: auto` is scrolled by a pointer for free and
       * by a keyboard only if focus can enter it. Before this, the sole focusable
       * descendant was the "Download CSV" button, which sits OUTSIDE the
       * overflowing content — so at a 412px viewport the right-hand 56px of the
       * table was reachable by touch and by no key at all.
       *
       * axe's `scrollable-region-focusable` passed throughout, correctly by its
       * own definition: the region did contain focusable content. The rule's
       * PURPOSE is "a keyboard user can reach what is in here", and the element
       * satisfying it was not in the part that overflowed. Moving the button out
       * of the region is therefore part of the fix, not tidying — it is what makes
       * the detector's pass mean the thing the detector is for.
       *
       * `<section>` rather than `<div role="region">`, for the reason DataList
       * gives below: a native element carries the role implicitly and cannot lose
       * it to a typo. Named from the caption, so the region a screen reader
       * announces is the table the sighted reader sees, not a second name
       * invented for it.
       *
       * The tab stop is UNCONDITIONAL, and that is a deliberate trade. Whether
       * the table overflows is a fact about layout, which does not exist at render
       * time and differs between the server and client passes — a tabindex
       * conditioned on it would be a hydration mismatch that reports itself as an
       * accessibility feature. One extra tab stop on a table that happens to fit
       * is a smaller defect than content no key can reach.
       *
       * ON THE SUPPRESSION BELOW
       *   `noNoninteractiveTabindex` is right about the general case and wrong
       *   about this one. Its reasoning — "adding non-interactive elements to the
       *   keyboard navigation flow can confuse users" — assumes the element does
       *   nothing when focused. A scrolling container is the exception the rule
       *   does not model: focusing it is what makes the arrow keys scroll it, and
       *   it is the pattern WAI and axe's own documentation prescribe for exactly
       *   this. Suppressed at the line, with the measurement in BUG-033, rather
       *   than switched off in biome.json where the next table would inherit it.
       */}
      {/* biome-ignore lint/a11y/noNoninteractiveTabindex: a scrolling region must be focusable or its overflow is keyboard-unreachable — BUG-033. */}
      <section className="jl-table__scroll" tabIndex={0} aria-labelledby={captionId}>
        <table
          // +1 for the header row: aria-rowcount describes the grid, not the body.
          aria-rowcount={rows.length + 1}
          aria-describedby={captionId}
        >
          <caption id={captionId}>
            {caption}
            {virtualWindow ? (
              <span className="jl-visually-hidden">
                {` Showing ${visible.length} of ${rows.length} rows.`}
              </span>
            ) : null}
          </caption>
          <thead>
            <tr aria-rowindex={1}>
              {columns.map((column) => {
                const isSorted = sort?.key === column.key;
                return (
                  <th
                    key={column.key}
                    // `scope` is what associates a header with its column for a
                    // screen reader. Without it the header is just bold text.
                    scope="col"
                    // aria-sort goes on the header, and ONLY on the sorted one.
                    // Setting "none" on every other header is noise a screen reader
                    // announces on each cell.
                    aria-sort={isSorted ? sort.direction : undefined}
                  >
                    {column.sortable ? (
                      <button type="button" onClick={() => toggleSort(column.key)}>
                        {column.header}
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>{emptyMessage}</td>
              </tr>
            ) : (
              visible.map((row, offset) => (
                <tr
                  key={rowKey(row)}
                  // 1-based, and offset by the header row. This is the index within
                  // the WHOLE dataset, which is the point: a virtualised row 4,001
                  // must announce itself as 4,001, not as 3.
                  aria-rowindex={firstVisibleIndex + offset + 2}
                >
                  {columns.map((column, columnIndex) => {
                    const content = column.cell(row);
                    // The first column acts as the row header, so a screen reader
                    // reading a cell announces which row it belongs to.
                    return columnIndex === 0 ? (
                      <th key={column.key} scope="row">
                        {content}
                      </th>
                    ) : (
                      <td key={column.key}>{content}</td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      {/* Outside the scroll region deliberately — see the note above. */}
      <button type="button" onClick={exportCsv} className="jl-table__export">
        Download CSV
      </button>
    </div>
  );
}

export interface DataListProps<Row> {
  readonly caption: string;
  readonly columns: readonly TableColumn<Row>[];
  readonly rows: readonly Row[];
  readonly rowKey: (row: Row) => string;
}

/**
 * The narrow-viewport equivalent of the table.
 *
 * `<section aria-label>` rather than `role="region"` on a div: a native element
 * carries the role implicitly and cannot lose it to a typo, and the label is what
 * makes the region findable when navigating by landmark.
 *
 * A definition list per row, not a stack of divs: each column header stays
 * programmatically attached to its value, so the information is the same rather
 * than merely present. A responsive table that drops its headers on small
 * screens conveys strictly less than the wide one, which `REQ-A11Y-002` does not
 * permit.
 */
export function DataList<Row>({ caption, columns, rows, rowKey }: DataListProps<Row>) {
  return (
    <section className="jl-list" aria-label={caption}>
      <ul>
        {rows.map((row) => (
          <li key={rowKey(row)}>
            <dl>
              {columns.map((column) => (
                <div key={column.key} className="jl-list__pair">
                  <dt>{column.header}</dt>
                  <dd>{column.cell(row)}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
    </section>
  );
}
