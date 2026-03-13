'use client';

import useSWR from 'swr';

import { CollectionPriorityCard } from '@/components/CollectionPriorityCard';
import { EmptyState } from '@/components/EmptyState';
import { FlipTable } from '@/components/FlipTable';
import { FloorBuyTable } from '@/components/FloorBuyTable';
import { GrindRecommendationCard } from '@/components/GrindRecommendationCard';
import { LoadingState } from '@/components/LoadingState';
import { MarketMoversTable } from '@/components/MarketMoversTable';
import { MarketPhaseBanner } from '@/components/MarketPhaseBanner';
import { MetricCard } from '@/components/MetricCard';
import { RecommendationFeed } from '@/components/RecommendationFeed';
import { RequireAuth } from '@/components/RequireAuth';
import { RosterTargetsTable } from '@/components/RosterTargetsTable';
import { ACCESS_TOKEN_STORAGE_KEY, API_BASE_URL } from '@/lib/api';
import { useDashboard } from '@/hooks/useDashboard';
import { formatSignedStubs, formatStubs, marketPhaseLabels } from '@/lib/utils';

type DashboardMarketMover = {
  item_id: string;
  name: string;
  best_buy_price?: number | null;
  best_sell_price?: number | null;
  price_change: number;
  change_percent: number;
  liquidity_score?: number | null;
};

type DashboardMarketMoversResponse = {
  count: number;
  items: DashboardMarketMover[];
};

async function getDashboardMarketMovers(): Promise<DashboardMarketMoversResponse> {
  const headers = new Headers({ Accept: 'application/json' });
  const accessToken = typeof window === 'undefined' ? null : window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}/market/movers?limit=10`, {
    headers,
    cache: 'no-store',
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      const text = await response.text();
      if (text) message = text;
    }
    throw new Error(message);
  }

  return response.json() as Promise<DashboardMarketMoversResponse>;
}

function DashboardContent() {
  const {
    phase,
    topFlips,
    floors,
    rosterTargets,
    collections,
    portfolioRecommendations,
    grindRecommendation,
    inventory,
    trending,
  } = useDashboard();

  const marketMovers = useSWR('market-movers-dashboard', getDashboardMarketMovers, { refreshInterval: 60_000 });

  if (phase.isLoading && !phase.data) {
    return <LoadingState label="Loading dashboard..." />;
  }

  const topSells = (portfolioRecommendations.data ?? []).filter((item) => item.action === 'SELL').slice(0, 5);
  const phaseLabel = phase.data ? marketPhaseLabels[phase.data.current.phase] : 'Unknown';

  return (
    <div className="space-y-6">
      <MarketPhaseBanner phase={phase.data?.current} />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Market Phase" value={phaseLabel} hint={phase.data?.current.override_active ? 'Manual override active' : 'Auto-detected'} />
        <MetricCard title="Top Flips" value={String(topFlips.data?.count ?? 0)} hint="Live profit-per-minute leaders" />
        <MetricCard title="Inventory Value" value={formatStubs(inventory.data?.total_market_value ?? 0)} hint="Imported binder marked-to-market" />
        <MetricCard title="Inventory P/L" value={formatSignedStubs(inventory.data?.total_profit_loss ?? 0)} hint="Estimated gain/loss on imported cards" />
      </section>

      <section className="grid gap-6 2xl:grid-cols-2">
        <FlipTable title="Top Flip Opportunities" items={topFlips.data?.items ?? []} />
        <MarketMoversTable
          title="Trending Cards"
          items={trending.data?.items ?? []}
          emptyTitle="No trending cards yet"
          emptyDescription="StubIQ needs more live price history before trend scores become useful."
        />
      </section>

      <section className="grid gap-6 2xl:grid-cols-2">
        <MarketMoversTable
          title="Biggest Market Movers"
          items={marketMovers.data?.items ?? []}
          variant="market"
          emptyTitle="No market movers yet"
          emptyDescription="Market movers appear once the listing history captures significant sell-price changes."
        />
        <RecommendationFeed items={topSells} />
      </section>

      <section className="grid gap-6 2xl:grid-cols-2">
        <FloorBuyTable items={floors.data?.items ?? []} />
        <GrindRecommendationCard data={grindRecommendation.data} />
      </section>

      <section className="grid gap-6">
        <RosterTargetsTable items={rosterTargets.data?.items ?? []} />
        <CollectionPriorityCard data={collections.data} error={collections.error as Error | undefined} />
      </section>

      {phase.error && !phase.data ? (
        <EmptyState title="Dashboard data is unavailable" description="The API could not be reached. Verify the deployed backend is healthy and reachable from the configured base URL." />
      ) : null}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}
