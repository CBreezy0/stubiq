import type { Metadata } from 'next';

import '@/app/globals.css';

import { AppShell } from '@/components/AppShell';
import { Providers } from '@/app/providers';

export const metadata: Metadata = {
  title: 'MLB The Show Market Intel',
  description: 'Production-ready dashboard for the MLB The Show Diamond Dynasty market intelligence backend.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
