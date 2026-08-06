/**
 * Root layout — STEP-002.05 scaffold.
 *
 * The App Router requires a root layout providing <html> and <body>; without it
 * every page throws "Missing <html> and <body> tags in the root layout" at
 * runtime, even when the page itself renders correctly.
 *
 * Deliberately bare: no fonts, no design tokens, no shell. STEP-003 owns the
 * design system and replaces this.
 */

export const metadata = {
  title: 'JourneyLab',
  description: 'Trip digital twin — STEP-002.05 auth scaffold',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: '#fff', color: '#111' }}>{children}</body>
    </html>
  );
}
