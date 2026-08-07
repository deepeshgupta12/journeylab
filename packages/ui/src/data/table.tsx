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
